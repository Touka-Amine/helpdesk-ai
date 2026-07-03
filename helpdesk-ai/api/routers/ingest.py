# api/routers/ingest.py
"""Endpoint Power Automate — ingestion de tickets depuis email."""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.config import settings
from api.db.database import get_db
from api.db.models import Ticket, User
from api.services.ai_service import predict_and_recommend

router = APIRouter(prefix="/ingest", tags=["Power Automate"])


class IngestRequest(BaseModel):
    titre      : str = Field(..., min_length=3,  max_length=255,
                             example="VPN inaccessible depuis ce matin")
    description: str = Field(..., min_length=10,
                             example="Impossible de se connecter au VPN depuis 8h00")
    demandeur  : str = Field(default="", max_length=255)
    priorite   : str = Field(default="Modéré", max_length=50)
    filiale    : str = Field(default="", max_length=100)


def _verify_api_key(x_api_key: str = Header(default=None)) -> None:
    """Vérifie l'API key Power Automate (header X-Api-Key)."""
    if not x_api_key or x_api_key != settings.INGEST_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API key manquante ou invalide — header X-Api-Key requis",
        )


@router.post(
    "/",
    summary="Ingest ticket depuis Power Automate",
    response_description="Ticket créé avec prédiction et recommandation RAG",
)
def ingest_from_email(
    data: IngestRequest,
    db  : Session = Depends(get_db),
    _   : None    = Depends(_verify_api_key),
):
    """
    Endpoint appelé par Power Automate à la réception d'un email IT.

    - Authentification : header **X-Api-Key** (clé configurée dans `.env`)
    - Prédit la catégorie, recommande une solution via RAG sémantique
    - Enregistre le ticket dans la base SQLite sous l'utilisateur système
    - Retourne la prédiction + solution RAG + ID du ticket créé
    """
    pred = predict_and_recommend(data.titre, data.description)

    # Utilisateur système créé par init_db() — représente Power Automate
    sys_user = db.query(User).filter(User.email == "system@helpdesk-ai.local").first()
    if not sys_user:
        raise HTTPException(
            503,
            "Utilisateur système non initialisé — redémarrer l'API pour créer l'utilisateur système",
        )

    ticket = Ticket(
        user_id          = sys_user.id,
        titre            = data.titre[:255],
        description      = data.description,
        priorite_saisie  = data.priorite[:50],
        filiale          = data.filiale[:100],
        categorie_predite= (pred.get("categorie_ml") or pred.get("categorie", ""))[:50],
        categorie_finale = pred.get("categorie", "")[:50],
        confiance        = pred.get("confiance", 0.0),
        statut           = "En attente",
        solution_rag     = pred.get("solution", ""),
        knowledge_rag    = pred.get("knowledge", ""),
        created_at       = datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id"     : ticket.id,
        "saved_to_db"   : True,
        "prediction"    : {
            "categorie"  : pred.get("categorie"),
            "confiance"  : pred.get("confiance"),
            "auto_routed": pred.get("auto_routed"),
        },
        "solution_rag"  : pred.get("solution", ""),
        "needs_approval": pred.get("low_confidence", True),
    }
