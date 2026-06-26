"""RAG engine used by the API and notebooks."""

from __future__ import annotations

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGEngine:
    """
    Moteur de recommandation par similarite cosinus.
    Suggere les resolutions historiques les plus proches
    d'un nouveau ticket entrant.
    """

    def __init__(self, top_k: int = 3, similarity_threshold: float = 0.30) -> None:
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix = None
        self.knowledge_base: pd.DataFrame | None = None

    def fit(self, df: pd.DataFrame) -> "RAGEngine":
        """
        Construit la base de connaissance a partir des tickets resolus.
        df doit contenir : text_rag, Categorie, Resolution/Motif, knowledge Base
        """
        # Filtrer les lignes avec text_rag non-vide
        self.knowledge_base = df[
            df["text_rag"].notna() & (df["text_rag"] != "")
        ].reset_index(drop=True)

        # Vectoriser la base de connaissance
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.knowledge_base["text_rag"]
        )

        print("✅ RAG Engine fitted")
        print(f"   Base de connaissance : {len(self.knowledge_base)} tickets")
        print(f"   Matrice TF-IDF       : {self.tfidf_matrix.shape}")
        return self

    def recommend(
        self,
        query_text: str,
        category_filter: str | None = None,
        allow_fallback: bool = True,
    ) -> list:
        if not query_text or query_text.strip() == "":
            return []
        if self.vectorizer is None or self.tfidf_matrix is None or self.knowledge_base is None:
            raise RuntimeError("RAGEngine not fitted")

        query_vec = self.vectorizer.transform([query_text])

        if category_filter:
            mask = self.knowledge_base["Catégorie"] == category_filter
            if mask.sum() == 0:
                mask = pd.Series([True] * len(self.knowledge_base))
        else:
            mask = pd.Series([True] * len(self.knowledge_base))

        kb_filtered = self.knowledge_base[mask].reset_index(drop=True)
        matrix_filtered = self.tfidf_matrix[mask.values]

        scores = cosine_similarity(query_vec, matrix_filtered).flatten()
        top_indices = scores.argsort()[::-1]

        results = []
        seen_resolutions = set()

        for idx in top_indices:
            if len(results) >= self.top_k:
                break

            score = float(scores[idx])
            if score < self.similarity_threshold:
                break

            row = kb_filtered.iloc[idx]
            resolution = str(row["Résolution/Motif"]).strip()

            # Gestion des resolutions vides
            if resolution.lower() in ("nan", "none", ""):
                resolution = str(row["knowledge Base"]).strip()

            if resolution.lower() in ("nan", "none", ""):
                continue

            if resolution in seen_resolutions:
                continue
            seen_resolutions.add(resolution)

            results.append(
                {
                    "score": round(score, 4),
                    "categorie": row["Catégorie"],
                    "resolution": resolution,
                    "knowledge": str(row["knowledge Base"]),
                    "titre": str(row["Titre"]),
                }
            )

        # Fallback si 0 resultats : seuil abaisse a 0.10
        if allow_fallback and len(results) == 0 and self.similarity_threshold > 0.10:
            scores_sorted = scores.argsort()[::-1][: self.top_k]
            seen_resolutions = set()

            for idx in scores_sorted:
                score = float(scores[idx])
                if score < 0.10:
                    break

                row = kb_filtered.iloc[idx]
                resolution = str(row["Résolution/Motif"]).strip()

                if resolution.lower() in ("nan", "none", ""):
                    resolution = str(row["knowledge Base"]).strip()

                if resolution.lower() in ("nan", "none", ""):
                    continue

                if resolution in seen_resolutions:
                    continue
                seen_resolutions.add(resolution)

                results.append(
                    {
                        "score": round(score, 4),
                        "categorie": row["Catégorie"],
                        "resolution": resolution,
                        "knowledge": str(row["knowledge Base"]),
                        "titre": str(row["Titre"]),
                        "fallback": True,
                    }
                )

        return results

    def save(self, path: str) -> None:
        joblib.dump(self, path)
        print(f"✅ RAG Engine sauvegarde : {path}")

    @staticmethod
    def load(path: str) -> "RAGEngine":
        engine = joblib.load(path)
        print(f"✅ RAG Engine charge : {path}")
        return engine

