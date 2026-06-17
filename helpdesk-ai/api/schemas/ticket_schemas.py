"""Ticket schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TicketInput(BaseModel):
    titre: str = Field(..., min_length=3, example="Erreur activation Office 365")
    description: str = Field(
        ...,
        min_length=10,
        example="Microsoft Office affiche message produit non active",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "titre": "Probleme connexion VPN",
                "description": "Impossible de se connecter au VPN depuis hier soir",
            }
        }


class TicketCreate(BaseModel):
    titre: str = Field(..., min_length=5)
    description: str = Field(..., min_length=30)
    priorite: str = "Modere"
    filiale: str = ""
    equipement: str = ""


class TicketOut(BaseModel):
    id: int
    titre: str
    description: str
    priorite_saisie: str
    filiale: str = ""
    equipement: str = ""
    statut: str
    categorie_predite: Optional[str] = None
    categorie_finale: Optional[str] = None
    confiance: Optional[float] = None
    solution_rag: str = ""
    knowledge_rag: str = ""
    created_at: Optional[str | datetime] = None
    date_resolution: Optional[str | datetime] = None
    commentaire_client: str = ""
    commentaire_interne: str = ""
    classification: str = "Demande"


class ApproveRequest(BaseModel):
    statut: str
    categorie_finale: Optional[str] = None
    commentaire: Optional[str] = None
    commentaire_client: Optional[str] = None
    commentaire_interne: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    statut: str


class TicketHistoryItem(BaseModel):
    id: int
    champ: str
    ancienne_valeur: Optional[str] = None
    nouvelle_valeur: Optional[str] = None
    timestamp: datetime
    par: str = "Systeme"
