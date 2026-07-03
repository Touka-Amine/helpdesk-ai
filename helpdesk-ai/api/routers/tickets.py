from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import Ticket, User, TicketHistory
from api.db.nosql_store import archive_resolved_ticket, get_stats as nosql_stats, get_all_resolved
from api.routers.auth import get_current_user, require_admin
from api.schemas.ticket_schemas import ApproveRequest, TicketCreate, TicketOut
from api.services.ai_service import predict_and_recommend, recommend_for_category
from api.services.ticket_service import ticket_to_dict

# Statuts valides et transitions permises
VALID_STATUSES = ["En attente", "Prise en Charge", "Résolu", "Rejeté", "Problème"]
STATUS_TRANSITIONS = {
    "En attente": ["Prise en Charge", "Rejeté"],
    "Prise en Charge": ["Résolu", "Problème", "En attente"],
    "Problème": ["Prise en Charge", "Résolu"],
    "Résolu": [],
    "Rejeté": [],
}

def _log_ticket_history(db: Session, ticket_id: int, changed_by: int, field: str, old_value, new_value):
    """Enregistre un changement dans l'historique du ticket."""
    if old_value == new_value:
        return
    history = TicketHistory(
        ticket_id=ticket_id,
        changed_by=changed_by,
        champ_modifie=field,
        ancienne_valeur=str(old_value) if old_value is not None else None,
        nouvelle_valeur=str(new_value) if new_value is not None else None,
        timestamp=datetime.utcnow()
    )
    db.add(history)
    db.flush()


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/", response_model=TicketOut)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pred = predict_and_recommend(data.titre, data.description)

    ticket = Ticket(
        user_id=user.id,
        titre=data.titre,
        description=data.description,
        priorite_saisie=data.priorite,
        filiale=data.filiale,
        equipement=data.equipement,
        categorie_predite=pred.get("categorie_ml", pred.get("categorie", "")),
        categorie_finale=pred.get("categorie", ""),
        confiance=pred.get("confiance", 0),
        statut="En attente",
        solution_rag=pred.get("solution", ""),
        knowledge_rag=pred.get("knowledge", ""),
        created_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Log initial
    _log_ticket_history(db, ticket.id, None, "statut", None, "En attente")
    _log_ticket_history(db, ticket.id, None, "categorie_finale", None, pred.get("categorie", ""))
    db.commit()
    
    return ticket_to_dict(ticket)


@router.get("/me")
def get_my_tickets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == user.id)
        .order_by(Ticket.id.desc())
        .all()
    )
    return [ticket_to_dict(ticket) for ticket in tickets]


@router.get("/{ticket_id}")
def get_my_ticket_detail(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id, Ticket.user_id == user.id)
        .first()
    )
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")
    return ticket_to_dict(ticket)


@router.patch("/{ticket_id}/approve")
def approve_ticket(
    ticket_id: int,
    body: ApproveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")

    # Valider la transition de statut
    new_status = body.statut
    if new_status not in VALID_STATUSES:
        raise HTTPException(400, f"Statut invalide. Statuts permis: {VALID_STATUSES}")
    
    current_status = ticket.statut or "En attente"
    if new_status not in STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            400, 
            f"Transition non permise: {current_status} → {new_status}. "
            f"Transitions permises depuis {current_status}: {STATUS_TRANSITIONS.get(current_status, [])}"
        )

    # Log du changement de statut
    _log_ticket_history(db, ticket.id, admin.id, "statut", ticket.statut, new_status)
    ticket.statut = new_status
    
    # Gestion de la catégorie
    previous_category = ticket.categorie_finale or ticket.categorie_predite or ""
    threshold = 0.40
    allow_fallback = not (ticket.confiance is not None and ticket.confiance < threshold)
    
    if body.categorie_finale and body.categorie_finale != previous_category:
        _log_ticket_history(db, ticket.id, admin.id, "categorie_finale", previous_category, body.categorie_finale)
        ticket.categorie_finale = body.categorie_finale
        rec = recommend_for_category(
            ticket.titre,
            ticket.description,
            body.categorie_finale,
            allow_fallback=allow_fallback,
        )
        ticket.solution_rag = rec.get("solution", "")
        ticket.knowledge_rag = rec.get("knowledge", "")
        _log_ticket_history(db, ticket.id, admin.id, "solution_rag", None, "(mise à jour)")
    elif ticket.confiance is not None and ticket.confiance < threshold:
        rec = recommend_for_category(
            ticket.titre,
            ticket.description,
            ticket.categorie_finale,
            allow_fallback=allow_fallback,
        )
        ticket.solution_rag = rec.get("solution", "")
        ticket.knowledge_rag = rec.get("knowledge", "")
    
    # Commentaires client (réponse IT)
    if body.commentaire_client or body.commentaire:
        old_comment = ticket.commentaire_client
        new_comment = body.commentaire_client or body.commentaire or ""
        ticket.commentaire_client = new_comment
        _log_ticket_history(db, ticket.id, admin.id, "commentaire_client", old_comment, new_comment[:100])
    
    # Commentaires admin (notes internes)
    if hasattr(ticket, "commentaire_admin"):
        old_admin_comment = ticket.commentaire_admin
        new_admin_comment = body.commentaire_interne or ""
        ticket.commentaire_admin = new_admin_comment
        _log_ticket_history(db, ticket.id, admin.id, "commentaire_admin", old_admin_comment, new_admin_comment[:100])
    
    ticket.approved_by = str(admin.id)
    
    # Marquer comme résolu + archiver dans TinyDB
    if new_status == "Résolu":
        ticket.resolved_at = datetime.utcnow()
        archive_resolved_ticket(
            ticket_id          = ticket.id,
            titre              = ticket.titre,
            description        = ticket.description,
            categorie          = ticket.categorie_finale or ticket.categorie_predite or "",
            confiance          = ticket.confiance,
            solution           = ticket.solution_rag or "",
            knowledge          = ticket.knowledge_rag or "",
            filiale            = ticket.filiale or "",
            equipement         = ticket.equipement or "",
            commentaire_client = ticket.commentaire_client or "",
            approved_by        = str(admin.id),
        )

    db.commit()
    return {"message": "Ticket mis à jour", "id": ticket_id, "nouveau_statut": new_status}


@router.post("/{ticket_id}/refresh-rag")
def refresh_rag(
    ticket_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")

    threshold = 0.40
    category_filter = ticket.categorie_finale or ticket.categorie_predite or None
    allow_fallback = True
    if ticket.confiance is not None and ticket.confiance < threshold:
        category_filter = None
        allow_fallback = False

    rec = recommend_for_category(
        ticket.titre,
        ticket.description,
        category_filter,
        allow_fallback=allow_fallback,
    )
    old_solution = ticket.solution_rag
    ticket.solution_rag = rec.get("solution", "")
    ticket.knowledge_rag = rec.get("knowledge", "")
    _log_ticket_history(db, ticket.id, admin.id, "solution_rag", old_solution[:50] if old_solution else None, "(MAJ RAG)")
    db.commit()
    return {
        "message": "RAG mis a jour",
        "id": ticket_id,
        "solution_rag": ticket.solution_rag,
        "knowledge_rag": ticket.knowledge_rag,
    }


@router.get("/admin/all")
def get_all_tickets(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
    return [ticket_to_dict(ticket) for ticket in tickets]


@router.get("/{ticket_id}/history")
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne l'historique de modification d'un ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")
    
    # Verifier que l'utilisateur est proprietaire ou admin
    if ticket.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Acces refuse")
    
    history = (
        db.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.timestamp.asc())
        .all()
    )
    
    return [
        {
            "id": h.id,
            "champ": h.champ_modifie,
            "ancienne_valeur": h.ancienne_valeur,
            "nouvelle_valeur": h.nouvelle_valeur,
            "timestamp": h.timestamp,
            "par": f"Admin #{h.changed_by}" if h.changed_by else "Systeme"
        }
        for h in history
    ]


# ── Endpoints NoSQL (TinyDB) ───────────────────────────────────────────────────

@router.get("/resolved/stats")
def get_resolved_stats(_: User = Depends(require_admin)):
    """
    KPIs agrégés des tickets résolus archivés dans TinyDB.
    Retourne : total, répartition par catégorie, par filiale.
    """
    return nosql_stats()


@router.get("/resolved/archive")
def get_resolved_archive(
    limit: int = 50,
    _: User = Depends(require_admin),
):
    """
    Liste des tickets résolus archivés dans TinyDB (les plus récents en premier).
    Constitue la mémoire institutionnelle des résolutions approuvées.
    """
    docs = get_all_resolved(limit=limit)
    return {"total": len(docs), "tickets": docs}
