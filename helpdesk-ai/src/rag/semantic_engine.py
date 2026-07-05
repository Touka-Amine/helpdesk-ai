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
        similarity_threshold: float = 0.50,   # relevé 0.30→0.50 : filtre les suggestions peu pertinentes
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
            cat_index = cat_data["index"]
            cat_positions = cat_data["positions"]
            k = min(self.top_k * 3, cat_index.ntotal)   # récupérer + pour filtrer doublons
            scores_arr, local_ids = cat_index.search(q_vec, k)
            scores_flat = scores_arr[0]
            # Mapper local_ids → lignes de knowledge_base
            global_ids = [cat_positions[i] for i in local_ids[0] if i >= 0]
        else:
            # Fallback : pas de filtre catégorie
            category_filter = None
            k = min(self.top_k * 3, self._index.ntotal)
            scores_arr, local_ids = self._index.search(q_vec, k)
            scores_flat = scores_arr[0]
            global_ids = [i for i in local_ids[0] if i >= 0]

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
