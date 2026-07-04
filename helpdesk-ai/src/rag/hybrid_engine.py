"""
RAG Hybride — Phase 13 (Optimisation).

Combine le moteur sémantique (FAISS + embeddings) et le moteur lexical (TF-IDF)
par fusion de scores pondérée :

    score_hybride = alpha × score_sémantique + (1 - alpha) × score_lexical

Motivation : le sémantique capture la proximité de sens (score cosinus élevé),
mais le lexical retrouve mieux les tickets répétitifs exacts (P@3 et MRR plus hauts).
L'hybride combine les deux forces et améliore P@3, MRR, et Answer Relevancy.

Résultats attendus (à mesurer avec 07_rag_evaluation.ipynb) :
    P@3     : > 0.42 lexical baseline
    MRR@3   : > 0.65 lexical baseline
    score   : > 0.69 sémantique baseline
"""

from __future__ import annotations

from typing import Optional

from .engine import RAGEngine
from .semantic_engine import SemanticRAGEngine

import pandas as pd


class HybridRAGEngine:
    """
    Moteur RAG hybride : fusion linéaire score sémantique + lexical.

    Usage :
        engine = HybridRAGEngine(alpha=0.5)
        engine.fit(df)
        results = engine.recommend(query, category_filter="Réseau")
    """

    def __init__(
        self,
        alpha: float = 0.5,
        top_k: int = 3,
        similarity_threshold: float = 0.50,
        sem_model_name: str = "paraphrase-multilingual-mpnet-base-v2",
    ) -> None:
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha doit être dans [0, 1], reçu : {alpha}")
        self.alpha = alpha
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        self._sem = SemanticRAGEngine(
            model_name=sem_model_name,
            top_k=top_k * 5,          # récupérer plus pour la fusion
            similarity_threshold=0.0,  # pas de filtre ici, on filtre après fusion
        )
        self._lex = RAGEngine(
            top_k=top_k * 5,
            similarity_threshold=0.0,
        )
        self._fitted = False

    def fit(self, df: pd.DataFrame) -> "HybridRAGEngine":
        """Ajuste les deux sous-moteurs sur la même base de connaissance."""
        self._sem.fit(df)
        self._lex.fit(df)
        self._fitted = True
        print(f"HybridRAGEngine ajusté — alpha={self.alpha} | {len(df)} tickets")
        return self

    def recommend(
        self,
        query_text: str,
        category_filter: Optional[str] = None,
        allow_fallback: bool = True,
    ) -> list[dict]:
        """
        Recommandations hybrides fusionnées.

        Algorithme :
        1. Interroger les deux moteurs (sans seuil de score) sur top_k×5 résultats
        2. Construire un dictionnaire {résolution → {score_sem, score_lex}}
        3. Calculer score_hybride = alpha×score_sem + (1-alpha)×score_lex
        4. Trier par score_hybride, appliquer le seuil, retourner top_k
        """
        if not self._fitted:
            raise RuntimeError("HybridRAGEngine non ajusté — appeler fit() d'abord")
        if not query_text or not query_text.strip():
            return []

        # Résultats bruts des deux moteurs — on force top_k large et seuil=0.0
        # pour que la fusion hybride ait suffisamment de candidats à re-classer.
        # Les engines partagés (predictor) ont leurs propres top_k/threshold ; on
        # les restaure après l'appel pour ne pas perturber les autres chemins.
        _saved_sem = (self._sem.top_k, self._sem.similarity_threshold)
        _saved_lex = (self._lex.top_k, self._lex.similarity_threshold)
        self._sem.top_k              = self.top_k * 5
        self._sem.similarity_threshold = 0.0
        self._lex.top_k              = self.top_k * 5
        self._lex.similarity_threshold = 0.0
        try:
            sem_results = self._sem.recommend(
                query_text, category_filter=category_filter, allow_fallback=False
            )
            lex_results = self._lex.recommend(
                query_text, category_filter=category_filter, allow_fallback=False
            )
        finally:
            self._sem.top_k, self._sem.similarity_threshold = _saved_sem
            self._lex.top_k, self._lex.similarity_threshold = _saved_lex

        # Index par résolution (clé de dédoublonnage)
        merged: dict[str, dict] = {}

        for r in sem_results:
            key = r["resolution"]
            if key not in merged:
                merged[key] = {**r, "score_sem": r["score"], "score_lex": 0.0}
            else:
                merged[key]["score_sem"] = r["score"]

        for r in lex_results:
            key = r["resolution"]
            if key not in merged:
                merged[key] = {**r, "score_sem": 0.0, "score_lex": r["score"]}
            else:
                merged[key]["score_lex"] = r["score"]

        # Calcul du score hybride et tri
        results = []
        for key, item in merged.items():
            hybrid_score = (
                self.alpha * item["score_sem"]
                + (1.0 - self.alpha) * item["score_lex"]
            )
            item["score"] = round(hybrid_score, 4)
            item["score_sem"] = round(item["score_sem"], 4)
            item["score_lex"] = round(item["score_lex"], 4)
            results.append(item)

        results.sort(key=lambda x: x["score"], reverse=True)

        # Appliquer le seuil
        filtered = [r for r in results if r["score"] >= self.similarity_threshold]

        # Fallback si aucun résultat au-dessus du seuil
        if allow_fallback and not filtered and results:
            fallback_threshold = 0.20
            filtered = [r for r in results if r["score"] >= fallback_threshold]
            for r in filtered:
                r["fallback"] = True

        return filtered[: self.top_k]

    def info(self) -> dict:
        """Métadonnées du moteur pour monitoring."""
        return {
            "engine": "HybridRAGEngine",
            "alpha": self.alpha,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "semantic_model": self._sem.model_name,
            "n_tickets": len(self._sem.knowledge_base) if self._sem.knowledge_base is not None else 0,
        }
