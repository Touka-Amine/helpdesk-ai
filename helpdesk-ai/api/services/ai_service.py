# api/services/ai_service.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data.preprocess import clean_text
from models.heuristics import apply_heuristics


def get_predictor():
    """Retourne l'instance singleton du Predictor (lazy-load si nécessaire)."""
    from api.predictor import predictor
    if not predictor._loaded:
        predictor.load()
    return predictor


def recommend_for_category(
    titre: str,
    description: str,
    categorie: str | None = None,
    allow_fallback: bool = True,
) -> dict:
    """
    Recommande une solution RAG pour une catégorie donnée.
    Utilise predictor.recommend() qui dispatch vers le moteur sémantique (FAISS)
    ou lexical (TF-IDF) selon disponibilité.
    """
    predictor = get_predictor()
    recs = predictor.recommend(titre, description, categorie, allow_fallback=allow_fallback)

    recommendations = []
    for i, rec in enumerate(recs, 1):
        resolution = rec.get("resolution", "")
        knowledge  = rec.get("knowledge", "")
        if not resolution or resolution.lower() in ("nan", "none"):
            resolution = knowledge
        recommendations.append({
            "rank"      : i,
            "score"     : rec["score"],
            "resolution": resolution,
            "knowledge" : knowledge,
            "fallback"  : rec.get("fallback", False),
        })

    return {
        "categorie"      : categorie,
        "solution"       : recommendations[0]["resolution"] if recommendations else "",
        "knowledge"      : recommendations[0]["knowledge"]  if recommendations else "",
        "recommendations": recommendations,
    }


def predict_and_recommend(titre: str, description: str) -> dict:
    """
    Pipeline complet : prédiction ML → heuristiques → recommandations RAG sémantique.

    Returns dict avec : categorie, categorie_ml, confiance, auto_routed,
                        low_confidence, heuristic_applied, solution, knowledge,
                        recommendations[].
    """
    predictor = get_predictor()

    # ── Prédiction ML ────────────────────────────────────────────────────────
    text_clean = clean_text(description)
    proba      = predictor.pipeline.predict_proba([text_clean])[0]
    pred_idx   = proba.argmax()
    categorie  = predictor.pipeline.classes_[pred_idx]
    confiance  = float(proba[pred_idx])

    # ── Heuristiques (texte brut non nettoyé pour FORCE_RULES regex) ─────────
    h = apply_heuristics(
        text_original      = f"{titre} {description}",
        predicted_category = categorie,
        confidence         = confiance,
        threshold          = predictor.threshold,
    )
    categorie_finale = h["categorie"]
    confiance_finale = h["confiance"]
    category_filter  = categorie_finale if confiance_finale >= 0.70 else None

    # ── RAG sémantique (via predictor.recommend → FAISS ou TF-IDF) ───────────
    recs = predictor.recommend(titre, description, category_filter)

    recommendations = []
    for i, rec in enumerate(recs, 1):
        resolution = rec.get("resolution", "")
        knowledge  = rec.get("knowledge", "")
        if not resolution or resolution.lower() in ("nan", "none"):
            resolution = knowledge
        recommendations.append({
            "rank"      : i,
            "score"     : rec["score"],
            "resolution": resolution,
            "knowledge" : knowledge,
            "fallback"  : rec.get("fallback", False),
        })

    return {
        "categorie"        : categorie_finale,
        "categorie_ml"     : categorie,
        "confiance"        : confiance_finale,
        "confiance_ml"     : confiance,
        "auto_routed"      : confiance_finale >= predictor.threshold,
        "low_confidence"   : confiance_finale < predictor.threshold,
        "heuristic_applied": h["heuristic_applied"],
        "heuristic_rule"   : h["heuristic_rule"],
        "solution"         : recommendations[0]["resolution"] if recommendations else "",
        "knowledge"        : recommendations[0]["knowledge"]  if recommendations else "",
        "recommendations"  : recommendations,
    }
