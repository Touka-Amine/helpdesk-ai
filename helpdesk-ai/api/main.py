# api/main.py
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.db.database import init_db
from api.predictor import predictor
from api.routers.admin import router as admin_router
from api.routers.auth import router as auth_router
from api.routers.ingest import router as ingest_router
from api.routers.tickets import router as tickets_router
from api.schemas import FullResponse, HealthResponse, TicketInput

# Rate limiting — voir api/middleware/auth_middleware.py (dépendance FastAPI)


def _chauffer_les_modeles() -> None:
    """Fait passer une requete factice dans toute la chaine, au demarrage.

    Charger un modele ne suffit pas a le rendre rapide. Le premier appel reel
    declenche encore l'allocation des tampons de `sentence-transformers`, le
    premier parcours de l'index FAISS et la mise en cache des vectoriseurs
    scikit-learn. La campagne de charge l'avait mesure sans le nommer : sur
    trente appels successifs, la mediane etait a 105 ms et le maximum a
    1 763 ms. Ce seul appel froid suffisait a porter le quatre-vingt-quinzieme
    centile a 330 ms et a faire echouer ENF-01.

    Le ticket factice ne touche ni la base ni le journal : il ne fait que
    traverser le predicteur et le moteur de recherche. Un echec ici n'empeche
    pas le service de demarrer — le premier vrai appel sera simplement lent,
    comme avant.
    """
    try:
        from api.services.ai_service import predict_and_recommend
        debut = time.perf_counter()
        predict_and_recommend(
            "Prechauffage du service",
            "Requete factice emise au demarrage pour amorcer les modeles, "
            "elle n'est ni enregistree ni comptabilisee.")
        print("Modeles chauffes en %.0f ms" % ((time.perf_counter() - debut) * 1000))
    except Exception as e:  # noqa: BLE001 — le demarrage ne doit jamais echouer ici
        print("Prechauffage ignore (%s) — le premier appel reel sera plus lent." % e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Controle avant toute autre chose : un service demarre en production avec les
    # secrets du fichier d'exemple serait ouvert a qui lit le depot.
    settings.verifier_secrets()
    init_db()
    predictor.load()
    _chauffer_les_modeles()
    yield


OPENAPI_TAGS = [
    {"name": "Accueil",        "description": "Santé et informations de l'API"},
    {"name": "Auth",           "description": "Authentification JWT — register / login"},
    {"name": "Tickets",        "description": "CRUD tickets IT + workflow approbation admin"},
    {"name": "Prédiction",     "description": "Classification NLP + recommandations RAG sémantique"},
    {"name": "Power Automate", "description": "Webhook d'ingestion de tickets depuis email"},
    {"name": "Monitoring",     "description": "Santé des modèles et métriques"},
    {"name": "Metadata",       "description": "Métadonnées du modèle (catégories, seuil)"},
]

app = FastAPI(
    title="Helpdesk AI API",
    description=(
        "Plateforme IA de routage et d'assistance à la résolution de tickets IT francophones. "
        "Classification CamemBERT-base + RAG sémantique FAISS (`paraphrase-multilingual-mpnet-base-v2`) "
        "+ Human-in-the-loop. **Version 1.1 — Phase 8**."
    ),
    version="1.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — origines configurables via CORS_ORIGINS dans .env ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Api-Key"],
)


# ── Routers — toutes les routes versionnées sous /api/v1 ──────────────────────
V1 = "/api/v1"
app.include_router(auth_router,    prefix=V1)
app.include_router(tickets_router, prefix=V1)
app.include_router(ingest_router,  prefix=V1)
app.include_router(admin_router,   prefix=V1)


# ── Racine ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Accueil"])
def root():
    """Page d'accueil — liens vers la documentation et les endpoints principaux."""
    return {
        "message" : "Helpdesk AI API v1.1",
        "docs"    : "/docs",
        "redoc"   : "/redoc",
        "api"     : "/api/v1",
        "health"  : "/api/v1/health",
        "predict" : "/api/v1/predict",
    }


# ── Health ────────────────────────────────────────────────────────────────────
@app.get(f"{V1}/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    """État des modèles ML et RAG."""
    return {
        "status"      : "ok",
        "model_loaded": predictor._loaded,
        "rag_loaded"  : predictor._loaded and predictor._semantic_rag_loaded,
        "version"     : "1.1.0",
    }


# ── Métadonnées ───────────────────────────────────────────────────────────────
@app.get(f"{V1}/categories", tags=["Metadata"])
def get_categories():
    """Catégories IT supportées par le modèle et seuil de confiance."""
    return {
        "categories": predictor.classes,
        "threshold" : predictor.threshold,
        "rag_engine": "SemanticRAG (FAISS)" if predictor._semantic_rag_loaded else "LexicalRAG (TF-IDF)",
    }


# ── Prédiction ────────────────────────────────────────────────────────────────
@app.post(f"{V1}/predict", response_model=FullResponse, tags=["Prédiction"])
def predict_ticket(ticket: TicketInput):
    """
    Classification NLP + recommandations RAG sémantique (sans enregistrement).

    - Retourne la catégorie prédite avec score de confiance
    - Retourne les solutions similaires issues de la base de connaissance (FAISS)
    """
    if not predictor._loaded:
        raise HTTPException(503, "Modèles non chargés — relancer le serveur")
    if len(ticket.description.strip()) < 10:
        raise HTTPException(422, "Description trop courte (minimum 10 caractères)")

    try:
        prediction = predictor.predict(ticket.titre, ticket.description)
        category_filter = None if prediction["low_confidence"] else prediction["categorie"]
        raw_recs = predictor.recommend(
            ticket.titre,
            ticket.description,
            category_filter,
            allow_fallback=not prediction["low_confidence"],
        )
        recommendations = [
            {
                "rank"      : i,
                "score"     : rec["score"],
                "resolution": rec.get("resolution", ""),
                "knowledge" : rec.get("knowledge", ""),
                "titre"     : rec.get("titre", ""),
                "fallback"  : rec.get("fallback", False),
            }
            for i, rec in enumerate(raw_recs, 1)
        ]
        if prediction["low_confidence"]:
            message = f"⚠️ Confiance faible ({prediction['confiance']:.0%}) — vérification humaine recommandée"
        else:
            message = f"✅ Routage automatique — confiance {prediction['confiance']:.0%}"

        return {
            "ticket_titre"   : ticket.titre,
            "prediction"     : prediction,
            "recommendations": recommendations,
            "message"        : message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erreur interne : {str(e)}")
