# api/services/ticket_service.py
"""Service tickets — sérialisation et logique métier."""

from api.db.models import Ticket


def ticket_to_dict(ticket: Ticket) -> dict:
    """Sérialise un ticket ORM vers un dict JSON-compatible."""
    cat_predite = getattr(ticket, "categorie_predite", "") or ""
    cat_finale  = getattr(ticket, "categorie_finale", "") or cat_predite
    return {
        "id"                 : ticket.id,
        "titre"              : ticket.titre,
        "description"        : ticket.description,
        "priorite_saisie"    : ticket.priorite_saisie or "",
        "filiale"            : getattr(ticket, "filiale", "") or "",
        "equipement"         : getattr(ticket, "equipement", "") or "",
        "categorie_predite"  : cat_predite,
        "categorie_finale"   : cat_finale,
        "confiance"          : getattr(ticket, "confiance", None),
        "solution_rag"       : getattr(ticket, "solution_rag", "") or "",
        "knowledge_rag"      : getattr(ticket, "knowledge_rag", "") or "",
        "statut"             : ticket.statut or "En attente",
        "created_at"         : ticket.created_at,
        "date_resolution"    : getattr(ticket, "resolved_at", None),
        "commentaire_client" : getattr(ticket, "commentaire_client", "") or "",
        "commentaire_interne": getattr(ticket, "commentaire_admin", "") or "",
        "classification"     : "",
    }
