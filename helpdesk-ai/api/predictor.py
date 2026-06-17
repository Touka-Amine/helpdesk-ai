# api/predictor.py

import joblib
import json
import os
import sys

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from data.preprocess import clean_text, build_text_for_rag
from rag.engine import RAGEngine

# Chemins
MODEL_PATH    = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_pipeline.pkl')
RAG_PATH      = os.path.join(os.path.dirname(__file__), '..', 'models', 'rag_engine.pkl')
META_PATH     = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_metadata.json')


class Predictor:
    """
    Singleton — chargé une seule fois au démarrage de l'API.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return

        print("🔄 Chargement des modèles...")
        # Legacy pickle compatibility: notebook-saved models reference __main__.RAGEngine
        import __main__
        __main__.RAGEngine = RAGEngine

        self.pipeline = joblib.load(MODEL_PATH)
        self.rag = joblib.load(RAG_PATH)

        with open(META_PATH, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        self.threshold = self.metadata.get('confidence_threshold', 0.40)
        self.classes   = self.metadata.get('classes', [])

        self._loaded = True
        print(f"✅ Pipeline chargé — seuil confiance : {self.threshold}")
        print(f"✅ RAG Engine chargé — {len(self.rag.knowledge_base)} tickets")

    def predict(self, titre: str, description: str) -> dict:
        """Prédit la catégorie d'un ticket."""

        text_clean = clean_text(description)

        proba      = self.pipeline.predict_proba([text_clean])[0]
        pred_idx   = proba.argmax()
        categorie  = self.pipeline.classes_[pred_idx]
        confiance  = float(proba[pred_idx])

        return {
            'categorie'     : categorie,
            'confiance'     : round(confiance, 4),
            'auto_routed'   : confiance >= self.threshold,
            'low_confidence': confiance < self.threshold
        }

    def recommend(
        self,
        titre: str,
        description: str,
        categorie: str | None,
        allow_fallback: bool = True,
    ) -> list:
        """Retourne les recommandations RAG."""

        text_rag = build_text_for_rag(description, titre=titre)
        return self.rag.recommend(
            query_text=text_rag,
            category_filter=categorie,
            allow_fallback=allow_fallback,
        )


# Instance globale
predictor = Predictor()