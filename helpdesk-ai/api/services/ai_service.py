# api/services/ai_service.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data.preprocess import clean_text, build_text_for_rag
from models.heuristics import apply_heuristics   # ← nouveau


def get_predictor():
    """
    Retourne l'instance singleton du Predictor.
    """
    from api.predictor import predictor
    if not predictor._loaded:
        predictor.load()
    return predictor


def recommend_for_category(titre: str, description: str, categorie: str = None, allow_fallback: bool = True) -> dict:
    """
    Recommande une solution pour une catégorie donnée (ou prédite si None).
    
    Args:
        titre: Titre du ticket
        description: Description du ticket
        categorie: Catégorie cible (si None, utilise la prédiction ML)
        allow_fallback: Si True, utilise le fallback RAG si pas de résultat
    
    Returns:
        Dict avec 'solution', 'knowledge', 'recommendations', etc.
    """
    predictor = get_predictor()
    
    # Si pas de catégorie spécifiée, faire une prédiction
    
    # ── RAG avec fallback control ────────────────────────────
    text_rag = build_text_for_rag(description, titre=titre)
    recs = predictor.rag.recommend(
        query_text      = text_rag,
        category_filter = categorie,
        allow_fallback  = allow_fallback
    )
    
    # Formater les recommandations
    recommendations = []
    for i, rec in enumerate(recs, 1):
        resolution = rec.get("resolution", "")
        knowledge  = rec.get("knowledge", "")
        if resolution.lower() in ("nan", "none", ""):
            resolution = knowledge
        recommendations.append({
            "rank"      : i,
            "score"     : rec["score"],
            "resolution": resolution,
            "knowledge" : knowledge,
            "fallback"  : rec.get("fallback", False)
        })
    
    return {
        "categorie"     : categorie,
        "solution"      : recommendations[0]["resolution"] if recommendations else "",
        "knowledge"     : recommendations[0]["knowledge"]  if recommendations else "",
        "recommendations": recommendations
    }


def predict_and_recommend(titre: str, description: str) -> dict:
    """
    Prédit la catégorie + applique les heuristiques + recommande via RAG.
    """
    from api.predictor import predictor
    if not predictor._loaded:
        predictor.load()

    # ── Prédiction ML ────────────────────────────────────────
    text_clean = clean_text(description)
    proba      = predictor.pipeline.predict_proba([text_clean])[0]
    pred_idx   = proba.argmax()
    categorie  = predictor.pipeline.classes_[pred_idx]
    confiance  = float(proba[pred_idx])

    # ── Heuristiques (sur texte original, pas nettoyé) ───────
    texte_brut = f"{titre} {description}"
    h = apply_heuristics(
        text_original      = texte_brut,
        predicted_category = categorie,
        confidence         = confiance,
        threshold          = predictor.threshold
    )

    categorie_finale = h["categorie"]
    confiance_finale = h["confiance"]
    category_filter = categorie_finale if confiance_finale >= 0.70 else None

    # ── RAG — filtré par catégorie finale ────────────────────
    text_rag = build_text_for_rag(description, titre=titre)
    recs = predictor.rag.recommend(
        query_text      = text_rag,
        category_filter = category_filter
    )

    # Formater les recommandations
    recommendations = []
    for i, rec in enumerate(recs, 1):
        resolution = rec.get("resolution", "")
        knowledge  = rec.get("knowledge", "")
        if resolution.lower() in ("nan", "none", ""):
            resolution = knowledge
        recommendations.append({
            "rank"      : i,
            "score"     : rec["score"],
            "resolution": resolution,
            "knowledge" : knowledge,
            "fallback"  : rec.get("fallback", False)
        })

    return {
        "categorie"          : categorie_finale,
        "categorie_ml"       : categorie,          # prédiction brute ML
        "confiance"          : confiance_finale,
        "confiance_ml"       : confiance,           # confiance brute ML
        "auto_routed"        : confiance_finale >= predictor.threshold,
        "low_confidence"     : confiance_finale < predictor.threshold,
        "heuristic_applied"  : h["heuristic_applied"],
        "heuristic_rule"     : h["heuristic_rule"],
        "classification"     : "Incident" if any(
            w in description.lower()
            for w in ["erreur", "impossible", "ne fonctionne", "bloqué", "panne"]
        ) else "Demande",
        "solution"           : recommendations[0]["resolution"] if recommendations else "",
        "knowledge"          : recommendations[0]["knowledge"]  if recommendations else "",
        "recommendations"    : recommendations
    }
