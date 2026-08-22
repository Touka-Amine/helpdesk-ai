"""Ticket schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "titre": "Probleme connexion VPN",
            "description": "Impossible de se connecter au VPN depuis hier soir",
        }
    })

    titre: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)


class TicketCreate(BaseModel):
    titre: str = Field(..., min_length=5)
    description: str = Field(..., min_length=30)
    priorite: str = "Modere"
    filiale: str = ""
    equipement: str = ""


class TicketOut(BaseModel):
    id: int
    cid: str = ""
    demandeur_nom: str = ""
    demandeur_email: str = ""
    titre: str
    description: str
    priorite_saisie: str
    priorite_predite: str = ""
    priorite_finale: Optional[str] = None
    filiale: str = ""
    equipement: str = ""
    statut: str
    categorie_predite: Optional[str] = None
    categorie_finale: Optional[str] = None
    confiance: Optional[float] = None
    solution_rag: str = ""
    knowledge_rag: str = ""
    rag_score: Optional[float] = None
    created_at: Optional[str | datetime] = None
    date_resolution: Optional[str | datetime] = None
    temps_ecoule: Optional[str] = None
    commentaire_client: str = ""
    commentaire_interne: str = ""
    classification: str = "Demande"
    classification_predite: str = "Demande"
    classification_finale: Optional[str] = None
    assigne_a: Optional[str] = None
    feedback_vote: Optional[str] = None
    feedback_comment: str = ""


class FeedbackRequest(BaseModel):
    vote: str = Field(..., pattern="^(up|down)$")
    comment: str = ""


class ApproveRequest(BaseModel):
    statut: str
    categorie_finale: Optional[str] = None
    priorite_finale: Optional[str] = None
    classification_finale: Optional[str] = None
    assigne_a: Optional[str] = None
    commentaire: Optional[str] = None
    commentaire_client: Optional[str] = None
    commentaire_interne: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    statut: str


class AdminTicketCreate(BaseModel):
    """
    Création d'un ticket par l'admin depuis le tableau. Le demandeur est soit un client
    déjà enregistré (demandeur_user_id), soit une personne sans compte (nom/prenom/email
    en saisie libre — un compte "fantôme" is_active=False est alors créé pour porter le
    ticket, cohérent avec le reste du schéma qui exige un user_id).
    """
    titre: str = Field(..., min_length=5)
    description: str = Field(..., min_length=10)
    priorite: str = "Modere"
    filiale: str = ""
    equipement: str = ""
    demandeur_user_id: Optional[int] = None
    demandeur_nom: Optional[str] = None
    demandeur_prenom: Optional[str] = None
    demandeur_email: Optional[str] = None


class RagSynthesisOut(BaseModel):
    text: str
    source: str  # "ollama" | "fallback" | "none"


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    # Historique de la conversation (question/reponse), sans le contexte du ticket ni le
    # system prompt — reconstruits cote serveur a chaque appel a partir de l'etat reel de
    # la base (cf. api/services/llm_service.py::chat_reply), jamais fournis par le client.
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=20)


class ChatResponseOut(BaseModel):
    reply: str
    source: str  # "ollama" | "fallback" | "none"


class TicketHistoryItem(BaseModel):
    id: int
    champ: str
    ancienne_valeur: Optional[str] = None
    nouvelle_valeur: Optional[str] = None
    timestamp: datetime
    par: str = "Systeme"
