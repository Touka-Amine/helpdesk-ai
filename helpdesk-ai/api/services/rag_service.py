# api/services/rag_service.py
"""Service RAG — abstraction du retrieval (sémantique ou lexical)."""


def get_rag_recommendations(
    titre: str,
    description: str,
    categorie: str | None = None,
    allow_fallback: bool = True,
) -> list:
    """
    Retourne les recommandations RAG pour un ticket.
    Dispatch vers le moteur sémantique (FAISS) si disponible, sinon lexical (TF-IDF).
    """
    from api.predictor import predictor
    if not predictor._loaded:
        predictor.load()
    return predictor.recommend(titre, description, categorie, allow_fallback=allow_fallback)


def rag_engine_info() -> dict:
    """Informations sur le moteur RAG actif (pour monitoring / health)."""
    from api.predictor import predictor
    if not predictor._loaded:
        return {"loaded": False, "engine": "non charge"}

    hybrid_active = predictor._semantic_rag_loaded and getattr(predictor, 'hybrid_rag', None) is not None
    sem_active    = predictor._semantic_rag_loaded and predictor.semantic_rag is not None

    if hybrid_active:
        engine_name = "HybridRAG (FAISS×0.5 + TF-IDF×0.5)"
    elif sem_active:
        engine_name = "SemanticRAG (FAISS)"
    else:
        engine_name = "LexicalRAG (TF-IDF)"

    return {
        "loaded"             : True,
        "semantic_available" : sem_active,
        "hybrid_active"      : hybrid_active,
        "engine"             : engine_name,
        "knowledge_base_size": (
            len(predictor.semantic_rag.knowledge_base)
            if sem_active
            else len(predictor.rag.knowledge_base)
        ),
    }
