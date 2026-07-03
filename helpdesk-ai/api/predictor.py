# api/predictor.py

import joblib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from data.preprocess import clean_text, build_text_for_rag
from rag.engine import RAGEngine
from rag.semantic_engine import SemanticRAGEngine

MODEL_PATH   = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_pipeline.pkl')
RAG_PATH     = os.path.join(os.path.dirname(__file__), '..', 'models', 'rag_engine.pkl')
META_PATH    = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_metadata.json')
SEM_RAG_DIR  = os.path.join(os.path.dirname(__file__), '..', 'models', 'semantic_rag')


class Predictor:
    """
    Singleton — chargé une seule fois au démarrage de l'API.
    Moteur de prédiction : pipeline ML (TF-IDF + classificateur sklearn).
    Moteur RAG : SemanticRAGEngine (FAISS + paraphrase-multilingual-mpnet-base-v2)
                 avec fallback sur RAGEngine lexical (TF-IDF) si FAISS indisponible.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._semantic_rag_loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return

        print("Chargement des modèles ML et RAG...")

        # Pickle compat: notebooks sauvegardés avec __main__.RAGEngine
        import __main__
        __main__.RAGEngine = RAGEngine

        self.pipeline = joblib.load(MODEL_PATH)
        self.rag = joblib.load(RAG_PATH)

        with open(META_PATH, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        self.threshold = self.metadata.get('confidence_threshold', 0.40)
        self.classes   = self.metadata.get('classes', [])

        # ── RAG sémantique (FAISS) — prioritaire ──────────────────────────────
        try:
            self.semantic_rag = SemanticRAGEngine.load(SEM_RAG_DIR)
            self._semantic_rag_loaded = True
            n_docs = len(self.semantic_rag.knowledge_base)
            print(f"RAG semantique charge — {n_docs} tickets FAISS (paraphrase-multilingual-mpnet-base-v2)")
        except Exception as e:
            print(f"RAG semantique non disponible ({e}) — fallback lexical actif")
            self.semantic_rag = None
            self._semantic_rag_loaded = False

        self._loaded = True
        print(f"Pipeline ML charge — {len(self.rag.knowledge_base)} tickets, seuil={self.threshold}")

    def predict(self, titre: str, description: str) -> dict:
        """Prédit la catégorie via le pipeline ML (TF-IDF + classificateur)."""
        text_clean = clean_text(description)
        proba      = self.pipeline.predict_proba([text_clean])[0]
        pred_idx   = proba.argmax()
        categorie  = self.pipeline.classes_[pred_idx]
        confiance  = float(proba[pred_idx])
        return {
            'categorie'     : categorie,
            'confiance'     : round(confiance, 4),
            'auto_routed'   : confiance >= self.threshold,
            'low_confidence': confiance < self.threshold,
        }

    def recommend(
        self,
        titre: str,
        description: str,
        categorie: str | None,
        allow_fallback: bool = True,
    ) -> list:
        """
        Recommandations RAG — moteur sémantique (FAISS) en priorité,
        fallback lexical (TF-IDF) si FAISS indisponible.
        """
        text_rag = build_text_for_rag(description, titre=titre)

        if self._semantic_rag_loaded and self.semantic_rag is not None:
            return self.semantic_rag.recommend(
                query_text=text_rag,
                category_filter=categorie,
                allow_fallback=allow_fallback,
            )

        return self.rag.recommend(
            query_text=text_rag,
            category_filter=categorie,
            allow_fallback=allow_fallback,
        )


predictor = Predictor()
