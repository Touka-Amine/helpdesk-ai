# api/services/ticket_service.py
"""Service tickets — sérialisation et logique métier."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api.db.models import Ticket, TicketHistory

# Classification par défaut — aucun modèle dédié n'existe pour ce champ (contrairement
# à la catégorie, prédite par ML) : c'est une valeur de départ que l'admin confirme ou
# corrige, au même titre que la priorité saisie par le client.
DEFAULT_CLASSIFICATION = "Demande"


def _format_temps_ecoule(debut: datetime | None, fin: datetime | None) -> str | None:
    """Formate une durée lisible (ex: '2j 4h', '35 min') entre deux timestamps."""
    if not debut:
        return None
    end = fin or datetime.now(timezone.utc)
    if debut.tzinfo is None:
        debut = debut.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    total_min = max(0, int((end - debut).total_seconds() // 60))
    if total_min < 60:
        return f"{total_min} min"
    total_h = total_min // 60
    if total_h < 24:
        return f"{total_h}h {total_min % 60}min"
    jours = total_h // 24
    return f"{jours}j {total_h % 24}h"


def _resume_du_ticket(ticket: Ticket) -> str:
    """Le resume extractif, ou la description si le module n'est pas disponible.

    Un echec ici ne doit jamais empecher d'afficher un ticket : l'administrateur
    retrouve alors la description complete, ce qu'il avait avant EF-11.
    """
    try:
        from models.resume import resumer
        return resumer(ticket.titre or "", ticket.description or "")["resume"]
    except Exception:
        return ticket.description or ""


def _signaux_du_ticket(ticket: Ticket) -> list:
    """Les signaux de gravite, ou rien si le module n'est pas disponible."""
    try:
        from models.signaux import libelles
        return libelles(ticket.titre or "", ticket.description or "")
    except Exception:
        return []


def ticket_to_dict(ticket: Ticket) -> dict:
    """Sérialise un ticket ORM vers un dict JSON-compatible."""
    cat_predite = getattr(ticket, "categorie_predite", "") or ""
    cat_finale  = getattr(ticket, "categorie_finale", "") or cat_predite
    prio_predite = ticket.priorite_saisie or ""
    prio_finale  = getattr(ticket, "priorite_finale", None) or prio_predite
    class_finale = getattr(ticket, "classification_finale", None) or DEFAULT_CLASSIFICATION
    demandeur = getattr(ticket, "user", None)
    resolved_at = getattr(ticket, "resolved_at", None)
    return {
        "id"                 : ticket.id,
        "cid"                : f"CID-{ticket.id}",
        "demandeur_nom"      : f"{demandeur.prenom} {demandeur.nom}".strip() if demandeur else "",
        "demandeur_email"    : demandeur.email if demandeur else "",
        "titre"              : ticket.titre,
        "description"        : ticket.description,
        "priorite_saisie"    : ticket.priorite_saisie or "",
        "priorite_predite"   : prio_predite,
        "priorite_finale"    : prio_finale,
        "filiale"            : getattr(ticket, "filiale", "") or "",
        "equipement"         : getattr(ticket, "equipement", "") or "",
        "categorie_predite"  : cat_predite,
        "categorie_finale"   : cat_finale,
        "confiance"          : getattr(ticket, "confiance", None),
        "solution_rag"       : getattr(ticket, "solution_rag", "") or "",
        "knowledge_rag"      : getattr(ticket, "knowledge_rag", "") or "",
        "rag_score"          : getattr(ticket, "rag_score", None),
        "statut"             : ticket.statut or "En attente",
        "created_at"         : ticket.created_at,
        "date_resolution"    : resolved_at,
        "temps_ecoule"       : _format_temps_ecoule(ticket.created_at, resolved_at),
        "commentaire_client" : getattr(ticket, "commentaire_client", "") or "",
        "commentaire_interne": getattr(ticket, "commentaire_admin", "") or "",
        "classification"     : class_finale,
        "classification_predite": DEFAULT_CLASSIFICATION,
        "classification_finale" : class_finale,
        "assigne_a"          : getattr(ticket, "assigne_a", None),
        "feedback_vote"      : getattr(ticket, "feedback_vote", None),
        "feedback_comment"   : getattr(ticket, "feedback_comment", "") or "",
        # Orientation selon l'index de confiance (EF-07). Les tickets crees avant
        # cette version n'en portent pas : ils sont rendus comme non orientes
        # plutot que supposes automatiques, ce qui serait une affirmation fausse.
        "routage"            : getattr(ticket, "routage", None),
        "motif_routage"      : getattr(ticket, "motif_routage", "") or "",
        # Resume extractif (EF-11) : la description privee de ses formules de
        # civilite. Calcule a la lecture plutot que stocke, parce qu'il ne
        # depend que du texte et que la liste des formules peut etre refaite.
        "resume"             : _resume_du_ticket(ticket),
        # Signaux de gravite enonces par le demandeur (EF-13). Ce n'est pas une
        # tonalite : le corpus n'en porte pas, et metrics/tonalite_eval.json le
        # mesure. Ce sont des faits releves tels quels dans le texte.
        "signaux_gravite"    : _signaux_du_ticket(ticket),
    }


def log_ticket_history(
    db: Session,
    ticket_id: int,
    changed_by,
    field: str,
    old_value,
    new_value,
) -> None:
    """Enregistre un changement dans l'historique du ticket. Idempotent si old == new."""
    if old_value == new_value:
        return
    db.add(TicketHistory(
        ticket_id       = ticket_id,
        changed_by      = changed_by,
        champ_modifie   = field,
        ancienne_valeur = str(old_value) if old_value is not None else None,
        nouvelle_valeur = str(new_value) if new_value is not None else None,
        timestamp       = datetime.now(timezone.utc),
    ))
    db.flush()
