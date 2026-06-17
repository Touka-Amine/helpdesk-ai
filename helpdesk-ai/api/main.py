# api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.db.database import init_db
from api.routers.auth import router as auth_router
from api.routers.tickets import router as tickets_router
from api.schemas import TicketInput, FullResponse, HealthResponse
from api.predictor import predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chargement au démarrage — une seule fois
    init_db()
    predictor.load()
    yield
    # Nettoyage à l'arrêt (optionnel)
    print("🛑 API arrêtée")


app = FastAPI(
    title       = "Helpdesk AI API",
    description = "Routage automatique et recommandations RAG pour tickets IT",
    version     = "1.0.0",
    lifespan    = lifespan
)

# CORS — autorise Streamlit à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(auth_router)
app.include_router(tickets_router)


@app.get("/", tags=["Accueil"])
def root():
    """Page d'accueil simple pour eviter le 404 sur la racine."""
    return {
        "message": "Bienvenue sur Helpdesk AI API",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
        "categories": "/categories"
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    """Vérifie que l'API et les modèles sont opérationnels."""
    return {
        "status"      : "ok",
        "model_loaded": predictor._loaded,
        "rag_loaded"  : predictor._loaded,
        "version"     : "1.0.0"
    }


@app.post("/predict", response_model=FullResponse, tags=["Prédiction"])
def predict_ticket(ticket: TicketInput):
    """
    Analyse un ticket IT et retourne :
    - La catégorie prédite avec score de confiance
    - Les solutions similaires issues de la base de connaissance
    """
    if not predictor._loaded:
        raise HTTPException(status_code=503,
                            detail="Modèles non chargés")

    # Validation minimale
    if len(ticket.description.strip()) < 10:
        raise HTTPException(status_code=422,
                            detail="Description trop courte")

    try:
        # Prédiction
        prediction = predictor.predict(ticket.titre, ticket.description)

        # Recommandations RAG filtrées par catégorie prédite
        category_filter = None if prediction["low_confidence"] else prediction["categorie"]
        allow_fallback = not prediction["low_confidence"]
        raw_recs = predictor.recommend(
            ticket.titre,
            ticket.description,
            category_filter,
            allow_fallback=allow_fallback,
        )

        # Formater les recommandations
        recommendations = []
        for i, rec in enumerate(raw_recs, 1):
            recommendations.append({
                "rank"      : i,
                "score"     : rec['score'],
                "resolution": rec.get('resolution', ''),
                "knowledge" : rec.get('knowledge', ''),
                "titre"     : rec.get('titre', ''),
                "fallback"  : rec.get('fallback', False)
            })

        # Message contextuel
        if prediction['low_confidence']:
            message = (
                f"⚠️ Confiance faible ({prediction['confiance']:.0%}) — "
                f"vérification humaine recommandée"
            )
        else:
            message = (
                f"✅ Routage automatique — "
                f"confiance {prediction['confiance']:.0%}"
            )

        return {
            "ticket_titre"   : ticket.titre,
            "prediction"     : prediction,
            "recommendations": recommendations,
            "message"        : message
        }

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur interne : {str(e)}")


@app.get("/categories", tags=["Metadata"])
def get_categories():
    """Retourne les catégories supportées par le modèle."""
    return {
        "categories" : predictor.classes,
        "threshold"  : predictor.threshold
    }

# Ajoute dans api/main.py

import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tickets.db')

@app.post("/ingest", tags=["Power Automate"])
def ingest_from_email(ticket: TicketInput,
                      demandeur: str = "",
                      priorite:  str = "Modéré",
                      filiale:   str = ""):
    """
    Endpoint appelé par Power Automate.
    Prédit, enregistre en base et retourne le résultat complet.
    """
    result, _ = predict_ticket(ticket)   # réutilise la logique existante

    pred = result['prediction']
    recs = result['recommendations']
    sol  = recs[0]['resolution'] if recs else ""
    kb   = recs[0]['knowledge']  if recs else ""

    con = sqlite3.connect(DB_PATH)
    cur = con.execute("""
        INSERT INTO tickets
        (titre,description,demandeur,priorite,filiale,
         categorie_predite,confiance,auto_routed,
         categorie_finale,statut,solution,knowledge,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        ticket.titre, ticket.description,
        demandeur, priorite, filiale,
        pred['categorie'], pred['confiance'],
        int(pred['auto_routed']), pred['categorie'],
        'Auto-routé' if pred['auto_routed'] else 'En attente',
        sol, kb,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    ticket_id = cur.lastrowid
    con.commit(); con.close()

    return {
        **result,
        "ticket_id"    : ticket_id,
        "saved_to_db"  : True,
        "needs_approval": pred['low_confidence']
    }
