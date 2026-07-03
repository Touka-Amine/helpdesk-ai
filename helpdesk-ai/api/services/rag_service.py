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
    return {
        "loaded"             : True,
        "semantic_available" : predictor._semantic_rag_loaded,
        "engine"             : "SemanticRAG (FAISS)" if predictor._semantic_rag_loaded else "LexicalRAG (TF-IDF)",
        "knowledge_base_size": (
            len(predictor.semantic_rag.knowledge_base)
            if predictor._semantic_rag_loaded and predictor.semantic_rag is not None
            else len(predictor.rag.knowledge_base)
        ),
    }
