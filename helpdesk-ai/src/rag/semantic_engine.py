"""
RAG sémantique — Phase 6.

Remplace le moteur lexical (TF-IDF + cosinus) par des embeddings denses
(sentence-transformers paraphrase-multilingual-mpnet-base-v2) indexés
avec FAISS pour une recherche approximative rapide.

Avantages vs TF-IDF :
  - Capture la proximité sémantique (ex. "imprimante bloquée" ≈ "impression en attente")
  - Robuste aux synonymes, fautes de frappe légères, formulations différentes
  - Filtre optionnel par catégorie (même logique que le moteur lexical)
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from unidecode import unidecode

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
EMBED_DIM = 768


class SemanticRAGEngine:
    """
    Moteur RAG sémantique : embeddings denses + index FAISS.

    Usage :
        engine = SemanticRAGEngine()
        engine.fit(df)                          # df avec colonnes text_rag, Catégorie, …
        results = engine.recommend(query, category_filter="Microsoft")
        engine.save("models/semantic_rag/")
        engine2 = SemanticRAGEngine.load("models/semantic_rag/")
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        top_k: int = 3,
        # Echelle propre a ce moteur : scores mesures de 0.49 a 0.70. Un seuil
        # calibre pour lui ne vaut pas pour le moteur hybride, dont la fusion
        # change l'echelle (cf. src/rag/hybrid_engine.py).
        similarity_threshold: float = 0.50,
    ) -> None:
        self.model_name = model_name
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        self._model: SentenceTransformer | None = None
        self._index: faiss.IndexFlatIP | None = None          # Inner Product sur vecteurs L2-normalisés ≡ cosinus
        self._index_with_cat: dict[str, faiss.IndexFlatIP] = {}  # index par catégorie
        self.knowledge_base: pd.DataFrame | None = None

    # ── chargement paresseux du modèle ────────────────────────────────────────

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            print(f"Chargement du modele d'embedding : {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _encode(self, texts: list[str]) -> np.ndarray:
        """Encode une liste de textes en vecteurs L2-normalisés (cosinus via IP)."""
        model = self._get_model()
        vecs = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,   # L2-norm → cosinus = produit scalaire
            convert_to_numpy=True,
        )
        return vecs.astype("float32")

    # ── construction de l'index ───────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "SemanticRAGEngine":
        """
        Construit la base de connaissance et l'index FAISS.

        df doit contenir : text_rag, Catégorie, Résolution/Motif, knowledge Base
        """
        kb = df[df["text_rag"].notna() & (df["text_rag"] != "")].reset_index(drop=True)
        self.knowledge_base = kb

        texts = kb["text_rag"].tolist()
        print(f"Encodage de {len(texts)} tickets...")
        vecs = self._encode(texts)

        # Index global
        self._index = faiss.IndexFlatIP(EMBED_DIM)
        self._index.add(vecs)

        # Index par catégorie (filtre rapide sans masque numpy)
        self._index_with_cat = {}
        for cat in kb["Catégorie"].unique():
            mask = kb["Catégorie"] == cat
            cat_vecs = vecs[mask.values]
            idx = faiss.IndexFlatIP(EMBED_DIM)
            idx.add(cat_vecs)
            self._index_with_cat[cat] = {
                "index": idx,
                "positions": kb[mask].index.tolist(),   # positions dans knowledge_base
            }

        print(f"Index FAISS construit : {self._index.ntotal} vecteurs ({EMBED_DIM}d)")
        print(f"Modele : {self.model_name}")
        return self

    # ── recommandation ────────────────────────────────────────────────────────

    def _voisins_jusqu_a_k_reponses(self, q_vec, index, positions):
        """Cherche assez de voisins pour que `top_k` RÉSOLUTIONS différentes en sortent.

        Pourquoi un élargissement variable et non un facteur fixe
        ---------------------------------------------------------
        La version précédente lisait `top_k * 3` voisins, soit neuf, « pour
        filtrer les doublons ». Ce facteur suppose une base où chaque réponse
        n'apparaît qu'une poignée de fois. Celle du projet n'est pas ainsi
        faite : 1 357 passages pour 46 résolutions distinctes, soit une
        trentaine de copies par réponse. Les neuf plus proches voisins d'une
        requête sont donc, presque toujours, neuf exemplaires de la même
        résolution — et le dédoublonnage n'en laissait qu'une.

        Mesuré sur les quarante requêtes du jeu d'évaluation, filtre de
        pertinence retiré pour isoler l'effet :

            voisins lus    réponses distinctes    requêtes servies au complet
                 9                1,57                    1 sur 40
                18                1,85                    7
                36                2,25                   13
                75                2,75                   30
               150                3,00                   40

        Il faut lire cent cinquante voisins, soit onze pour cent de l'index,
        pour que trois réponses différentes sortent de chaque requête. Un
        facteur écrit en dur se tromperait à la première évolution du corpus :
        l'élargissement double donc jusqu'à ce que le compte y soit, ou jusqu'à
        épuisement de l'index. La recherche FAISS sur treize cents vecteurs
        coûte quelques dizaines de microsecondes ; deux ou trois passes ne se
        mesurent pas sur le temps de réponse.
        """
        import numpy as np

        total = index.ntotal
        k = min(max(self.top_k * 3, 1), total)
        while True:
            scores_arr, local_ids = index.search(q_vec, k)
            bruts = [i for i in local_ids[0] if i >= 0]
            global_ids = [positions[i] for i in bruts] if positions is not None else bruts
            if k >= total:
                break
            # Compter ce qui sortirait réellement, c'est-à-dire après dédoublonnage.
            distinctes = set()
            for gid in global_ids:
                r = self._resolution_de(gid)
                if r:
                    distinctes.add(r)
                if len(distinctes) >= self.top_k:
                    break
            if len(distinctes) >= self.top_k:
                break
            k = min(k * 2, total)
        return global_ids, scores_arr[0]

    def _resolutions_indexees(self) -> list:
        """Les réponses de la base, une par ligne, calculées une seule fois.

        L'élargissement variable peut parcourir plusieurs centaines de lignes
        avant d'avoir ses `top_k` réponses différentes. Un `iloc` par ligne y
        coûterait des dizaines de millisecondes à chaque requête, sur un chemin
        déjà sous contrainte de temps de réponse (ENF-01). La liste est donc
        bâtie au premier besoin et conservée.
        """
        cache = getattr(self, "_cache_resolutions", None)
        if cache is not None and len(cache) == len(self.knowledge_base):
            return cache
        kb = self.knowledge_base
        principale = kb.get("Résolution/Motif")
        secours = kb.get("knowledge Base")
        cache = []
        for i in range(len(kb)):
            r = str(principale.iloc[i]).strip() if principale is not None else ""
            if r.lower() in ("nan", "none", ""):
                r = str(secours.iloc[i]).strip() if secours is not None else ""
            cache.append("" if r.lower() in ("nan", "none", "") else r)
        self._cache_resolutions = cache
        return cache

    def _resolution_de(self, gid) -> str:
        """La réponse portée par une ligne, ou une chaîne vide s'il n'y en a pas."""
        return self._resolutions_indexees()[gid]

    def recommend(
        self,
        query_text: str,
        category_filter: str | None = None,
        allow_fallback: bool = True,
    ) -> list[dict]:
        if not query_text or not query_text.strip():
            return []
        if self.knowledge_base is None or self._index is None:
            raise RuntimeError("SemanticRAGEngine non ajuste — appeler fit() d'abord")

        q_vec = self._encode([query_text])   # (1, 768)

        if category_filter and category_filter in self._index_with_cat:
            cat_data = self._index_with_cat[category_filter]
            global_ids, scores_flat = self._voisins_jusqu_a_k_reponses(
                q_vec, cat_data["index"], cat_data["positions"])
        else:
            # Fallback : pas de filtre catégorie
            category_filter = None
            global_ids, scores_flat = self._voisins_jusqu_a_k_reponses(
                q_vec, self._index, None)

        results = []
        seen_resolutions: set[str] = set()

        for rank, gid in enumerate(global_ids):
            if len(results) >= self.top_k:
                break

            score = float(scores_flat[rank])
            if score < self.similarity_threshold:
                break

            row = self.knowledge_base.iloc[gid]
            resolution = str(row.get("Résolution/Motif", "")).strip()
            if resolution.lower() in ("nan", "none", ""):
                resolution = str(row.get("knowledge Base", "")).strip()
            if resolution.lower() in ("nan", "none", ""):
                continue
            if resolution in seen_resolutions:
                continue
            seen_resolutions.add(resolution)

            results.append({
                "score": round(score, 4),
                "categorie": row["Catégorie"],
                "titre": str(row["Titre"]),
                "resolution": resolution,
                "knowledge": str(row.get("knowledge Base", "")),
            })

        # Fallback seuil abaissé (0.10) si 0 résultats
        if allow_fallback and not results:
            for rank, gid in enumerate(global_ids):
                if len(results) >= self.top_k:
                    break
                score = float(scores_flat[rank])
                if score < 0.10:
                    break
                row = self.knowledge_base.iloc[gid]
                resolution = str(row.get("Résolution/Motif", "")).strip()
                if resolution.lower() in ("nan", "none", ""):
                    resolution = str(row.get("knowledge Base", "")).strip()
                if resolution.lower() in ("nan", "none", ""):
                    continue
                if resolution in seen_resolutions:
                    continue
                seen_resolutions.add(resolution)
                results.append({
                    "score": round(score, 4),
                    "categorie": row["Catégorie"],
                    "titre": str(row["Titre"]),
                    "resolution": resolution,
                    "knowledge": str(row.get("knowledge Base", "")),
                    "fallback": True,
                })

        return results

    # ── persistance ──────────────────────────────────────────────────────────

    def save(self, directory: str) -> None:
        """Sauvegarde le moteur dans un dossier (index FAISS + métadonnées + KB)."""
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)

        # Index FAISS global
        faiss.write_index(self._index, str(out / "index.faiss"))

        # Index par catégorie
        # Nom de fichier translittéré en ASCII (unidecode) : les caractères accentués
        # dans un chemin passé à faiss.write_index() sont mal encodés par l'API C++
        # sous Windows (mojibake), rendant le fichier illisible une fois le dépôt
        # cloné/checkouté sur Linux. Le nom de catégorie affiché reste inchangé
        # (conservé tel quel comme clé de cat_meta et dans "categories").
        cat_meta = {}
        for cat, data in self._index_with_cat.items():
            safe = unidecode(cat).replace("/", "_").replace(" ", "_")
            faiss.write_index(data["index"], str(out / f"index_cat_{safe}.faiss"))
            cat_meta[cat] = {"positions": data["positions"], "file": f"index_cat_{safe}.faiss"}

        # Knowledge base
        self.knowledge_base.to_parquet(out / "knowledge_base.parquet", index=True)

        # Métadonnées
        meta = {
            "model_name": self.model_name,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "embed_dim": EMBED_DIM,
            "n_tickets": len(self.knowledge_base),
            "categories": list(self._index_with_cat.keys()),
            "cat_meta": cat_meta,
        }
        (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"SemanticRAGEngine sauvegarde : {out}")
        print(f"  Tickets indexes : {self._index.ntotal}")
        print(f"  Modele : {self.model_name}")

    @classmethod
    def load(cls, directory: str) -> "SemanticRAGEngine":
        """Recharge un moteur sauvegardé."""
        out = Path(directory)
        meta = json.loads((out / "metadata.json").read_text(encoding="utf-8"))

        engine = cls(
            model_name=meta["model_name"],
            top_k=meta["top_k"],
            similarity_threshold=meta["similarity_threshold"],
        )
        engine._index = faiss.read_index(str(out / "index.faiss"))
        engine.knowledge_base = pd.read_parquet(out / "knowledge_base.parquet")

        engine._index_with_cat = {}
        for cat, cat_data in meta["cat_meta"].items():
            engine._index_with_cat[cat] = {
                "index": faiss.read_index(str(out / cat_data["file"])),
                "positions": cat_data["positions"],
            }

        print(f"SemanticRAGEngine charge : {out}")
        print(f"  Tickets : {engine._index.ntotal} | Modele : {engine.model_name}")
        return engine
