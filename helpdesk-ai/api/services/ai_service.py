# api/services/ai_service.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data.preprocess import clean_text
from models.heuristics import apply_heuristics
from api.db.vector_store import query_similar

TOP_K = 3


def get_predictor():
    """Retourne l'instance singleton du Predictor (lazy-load si nécessaire)."""
    from api.predictor import predictor
    if not predictor._loaded:
        predictor.load()
    return predictor


def _build_recommendations(static_recs: list, query_text: str, categorie: str | None) -> list[dict]:
    """
    Construit la liste finale de recommandations en fusionnant :
      - les résultats statiques (FAISS/TF-IDF, corpus d'entraînement DVC)
      - les résultats live (ChromaDB, tickets résolus par les admins depuis le dernier
        `dvc repro` — recherchables immédiatement, sans réentraînement)

    Triées par score décroissant, tronquées au top K.
    """
    recommendations = []
    for rec in static_recs:
        resolution = rec.get("resolution", "")
        knowledge  = rec.get("knowledge", "")
        if not resolution or resolution.lower() in ("nan", "none"):
            resolution = knowledge
        recommendations.append({
            "score"     : rec["score"],
            "resolution": resolution,
            "knowledge" : knowledge,
            "fallback"  : rec.get("fallback", False),
            "source"    : rec.get("source", "static"),
        })

    for rec in query_similar(query_text, categorie=categorie, top_k=TOP_K):
        recommendations.append({
            "score"     : rec["score"],
            "resolution": rec.get("resolution", ""),
            "knowledge" : rec.get("knowledge", ""),
            "fallback"  : False,
            "source"    : "chroma_live",
        })

    recommendations.sort(key=lambda r: r["score"], reverse=True)
    recommendations = recommendations[:TOP_K]
    for i, rec in enumerate(recommendations, 1):
        rec["rank"] = i
    return recommendations


def get_live_candidates(titre: str, description: str, categorie: str | None, top_k: int = 3) -> list[dict]:
    """
    Candidats ChromaDB seuls (tickets réellement résolus, avec un ticket_id réel et
    explorable) — contrairement à `_build_recommendations()`, ne mélange pas le corpus
    statique d'entraînement (qui n'a pas d'ID de ticket associé). Utilisé par la synthèse
    IA "human-in-the-loop" (api/services/llm_service.py), dont chaque puce doit pointer
    vers un vrai ticket que l'admin peut ensuite ouvrir.
    """
    query_text = f"{titre}\n{description}"
    return query_similar(query_text, categorie=categorie, top_k=top_k)


def recommend_for_category(
    titre: str,
    description: str,
    categorie: str | None = None,
    allow_fallback: bool = True,
) -> dict:
    """
    Recommande une solution RAG pour une catégorie donnée.
    Utilise predictor.recommend() (moteur sémantique/lexical statique) fusionné avec
    la base de connaissances vectorielle live (ChromaDB, tickets résolus récemment).
    """
    predictor = get_predictor()
    recs = predictor.recommend(titre, description, categorie, allow_fallback=allow_fallback)

    query_text = f"{titre}\n{description}"
    recommendations = _build_recommendations(recs, query_text, categorie)

    return {
        "categorie"      : categorie,
        "solution"       : recommendations[0]["resolution"] if recommendations else "",
        "knowledge"      : recommendations[0]["knowledge"]  if recommendations else "",
        "rag_score"      : recommendations[0]["score"]      if recommendations else None,
        "recommendations": recommendations,
    }


def predict_and_recommend(titre: str, description: str) -> dict:
    """
    Pipeline complet : prédiction ML → heuristiques → recommandations RAG (statique +
    base de connaissances vectorielle live).

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

    # ── RAG (statique FAISS/TF-IDF + live ChromaDB) ───────────────────────────
    recs = predictor.recommend(titre, description, category_filter)
    query_text = f"{titre}\n{description}"
    recommendations = _build_recommendations(recs, query_text, category_filter)

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
        "rag_score"        : recommendations[0]["score"]      if recommendations else None,
        "recommendations"  : recommendations,
    }
