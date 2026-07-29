"""
Base de connaissances vectorielle des tickets résolus — ChromaDB.

Architecture à deux piliers :
  - PostgreSQL (SQLAlchemy) : base opérationnelle — intégrité relationnelle et
                              transactionnelle (utilisateurs, tickets en cours, historique)
  - ChromaDB                : base de connaissances vectorielle — recherche sémantique
                              du RAG hybride sur les tickets résolus

Contrairement à l'ancien stockage TinyDB (simple journal JSON, jamais relu par le RAG —
un ticket résolu n'était donc jamais réellement proposé aux tickets suivants avant un
réentraînement complet), cette collection est interrogée en direct par le pipeline de
recommandation (voir query_similar(), appelée depuis api/services/ai_service.py) : une
résolution admin devient exploitable par le RAG immédiatement, sans attendre un nouveau
`dvc repro` ni un redémarrage du serveur.

Mode embarqué (PersistentClient) : pas de serveur ChromaDB séparé, stockage dans
data/chroma/ (monté dans le même volume Docker que les modèles).
"""

import os
from datetime import datetime, timezone
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CHROMA_PATH = os.path.join(_BASE_DIR, "data", "chroma")
_COLLECTION_NAME = "resolved_tickets"
# Même modèle que SemanticRAGEngine (src/rag/semantic_engine.py) — espace vectoriel cohérent.
_EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"

_client = None
_embed_fn = None


def _get_embed_fn():
    """Modèle d'embedding — chargement paresseux, mis en cache (coûteux à recharger)."""
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=_EMBED_MODEL)
    return _embed_fn


def _get_collection():
    """
    Ouvre la collection Chroma. Le client persistant est mis en cache (connexion au
    fichier), mais la collection est ré-obtenue à chaque appel plutôt que mise en cache
    globalement : l'API tourne avec plusieurs workers uvicorn (processus séparés,
    Dockerfile.api --workers 2) — une collection mise en cache dans un worker ne voit
    pas les écritures faites par un autre worker tant qu'elle n'est pas ré-ouverte.
    """
    global _client
    if _client is None:
        os.makedirs(_CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_get_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )


# ── Écriture ───────────────────────────────────────────────────────────────────

def archive_resolved_ticket(
    ticket_id: int,
    titre: str,
    description: str,
    categorie: str,
    confiance: Optional[float],
    solution: str,
    knowledge: str,
    filiale: str = "",
    equipement: str = "",
    commentaire_client: str = "",
    approved_by: Optional[str] = None,
) -> None:
    """
    Calcule l'embedding [titre + description + solution] et l'ajoute à ChromaDB.

    Appelé en tâche de fond (BackgroundTasks, api/routers/tickets.py) quand statut →
    'Résolu' — le calcul de l'embedding (sentence-transformers) ne bloque jamais la
    réponse HTTP de l'admin.
    """
    collection = _get_collection()
    text = "\n".join(p for p in (titre, description, solution) if p).strip()
    if not text:
        return
    collection.upsert(
        ids=[str(ticket_id)],
        documents=[text],
        metadatas=[{
            "ticket_id"         : ticket_id,
            "titre"             : titre,
            "description"       : description,
            "categorie"         : categorie or "",
            "confiance_ml"      : round(confiance, 4) if confiance is not None else 0.0,
            "solution"          : solution or "",
            "knowledge"         : knowledge or "",
            "filiale"           : filiale or "",
            "equipement"        : equipement or "",
            "commentaire_client": commentaire_client or "",
            "approved_by"       : approved_by or "",
            "resolved_at"       : datetime.now(timezone.utc).isoformat(),
        }],
    )


# ── Recherche (utilisée par le RAG) ──────────────────────────────────────────────

def query_similar(text: str, categorie: Optional[str] = None, top_k: int = 3) -> list[dict]:
    """
    Recherche par similarité parmi les tickets résolus archivés. Permet aux résolutions
    récentes — pas encore présentes dans le corpus d'entraînement statique (FAISS/TF-IDF) —
    d'être proposées dès la prochaine requête similaire.

    Retourne une liste au même format que Predictor.recommend() (score/resolution/
    knowledge/fallback) pour pouvoir être fusionnée avec les recommandations statiques.
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0 or not text.strip():
        return []
    where = {"categorie": categorie} if categorie else None
    try:
        res = collection.query(query_texts=[text], n_results=min(top_k, count), where=where)
    except Exception:
        return []

    out: list[dict] = []
    ids = (res.get("ids") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]
    metadatas = (res.get("metadatas") or [[]])[0]
    for _id, dist, meta in zip(ids, distances, metadatas):
        similarity = max(0.0, 1.0 - dist)  # distance cosine -> similarite
        out.append({
            "score"     : round(similarity, 4),
            "resolution": meta.get("solution") or meta.get("knowledge") or "",
            "knowledge" : meta.get("knowledge", ""),
            "fallback"  : False,
            "source"    : "chroma_live",
        })
    return out


# ── Lecture / statistiques (mêmes signatures que l'ancien nosql_store.py) ───────

def get_all_resolved(limit: int = 100) -> list[dict]:
    """Retourne tous les tickets résolus (les plus récents en premier, limité)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    docs = collection.get(include=["metadatas"]).get("metadatas", [])
    return sorted(docs, key=lambda d: d.get("resolved_at", ""), reverse=True)[:limit]


def get_stats() -> dict:
    """
    Retourne les KPIs agrégés de la base de tickets résolus.
    Utilisé par l'endpoint /tickets/resolved/stats.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return {"total": 0, "par_categorie": {}, "par_filiale": {}}

    docs = collection.get(include=["metadatas"]).get("metadatas", [])
    par_categorie: dict[str, int] = {}
    par_filiale: dict[str, int] = {}
    for doc in docs:
        cat = doc.get("categorie") or "Inconnue"
        fil = doc.get("filiale") or "Inconnue"
        par_categorie[cat] = par_categorie.get(cat, 0) + 1
        par_filiale[fil] = par_filiale.get(fil, 0) + 1

    return {
        "total"        : len(docs),
        "par_categorie": dict(sorted(par_categorie.items(), key=lambda x: -x[1])),
        "par_filiale"  : dict(sorted(par_filiale.items(), key=lambda x: -x[1])),
    }


def count_resolved() -> int:
    """Nombre total de tickets résolus archivés."""
    return _get_collection().count()
