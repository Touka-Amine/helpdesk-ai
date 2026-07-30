import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import Ticket, User, TicketHistory
from api.db.vector_store import (
    archive_resolved_ticket, delete_resolved, get_stats as vector_stats, get_all_resolved,
)
from api.routers.auth import get_current_user, require_admin
from api.schemas.ticket_schemas import (
    AdminTicketCreate, ApproveRequest, FeedbackRequest, RagSynthesisOut, TicketCreate, TicketOut,
)
from api.services.ai_service import get_live_candidates, predict_and_recommend, recommend_for_category
from api.services.auth_service import hash_password
from api.services.llm_service import synthesize_recommendations
from api.services.ticket_service import ticket_to_dict, log_ticket_history

# Sous ce score de similarité RAG, on considère qu'aucun cas historique proche
# n'existe ("nouveau type de problème") — même seuil que HybridRAGEngine (predictor.py).
NOVELTY_THRESHOLD = 0.50

# Statuts valides et transitions permises
VALID_STATUSES = ["En attente", "Prise en Charge", "Résolu", "Rejeté", "Problème"]
STATUS_TRANSITIONS = {
    "En attente": ["Prise en Charge", "Rejeté"],
    "Prise en Charge": ["Résolu", "Problème", "Rejeté", "En attente"],
    "Problème": ["Prise en Charge", "Résolu", "Rejeté"],
    "Résolu": [],
    "Rejeté": [],
}

# Message automatique envoyé au client des que l'admin prend le ticket en charge —
# remplace la saisie manuelle d'un message a ce stade (le client est juste informe
# que sa demande est traitee ; le vrai message personnalise vient a la resolution).
AUTO_MESSAGE_PRISE_EN_CHARGE = "Votre ticket est en cours de traitement par notre équipe IT. Nous revenons vers vous rapidement."

# Message automatique de clôture — remplace le message générique de prise en charge
# si l'admin ne l'a pas explicitement personnalisé avant de résoudre le ticket.
AUTO_MESSAGE_RESOLU = "Votre ticket a été résolu par notre équipe IT. N'hésitez pas à nous recontacter si le problème persiste."


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
        rag_score=pred.get("rag_score"),
        created_at=datetime.now(timezone.utc),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Log initial
    log_ticket_history(db, ticket.id, None, "statut", None, "En attente")
    log_ticket_history(db, ticket.id, None, "categorie_finale", None, pred.get("categorie", ""))
    db.commit()

    return ticket_to_dict(ticket)


@router.post("/admin-create", response_model=TicketOut)
def admin_create_ticket(
    data: AdminTicketCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Création d'un ticket par un admin depuis le tableau (ex : appel téléphonique).
    Demandeur = client existant (demandeur_user_id) ou saisie libre (nom/prenom/email) —
    dans ce second cas, un compte client est créé automatiquement en is_active=False
    (pas de connexion possible : c'est un profil "trace", pas un vrai compte utilisateur)
    pour porter le ticket comme n'importe quel autre.
    """
    if data.demandeur_user_id:
        user = db.query(User).filter(User.id == data.demandeur_user_id).first()
        if not user:
            raise HTTPException(404, "Demandeur introuvable")
    else:
        if not (data.demandeur_nom and data.demandeur_prenom and data.demandeur_email):
            raise HTTPException(
                400,
                "Indiquez un client existant (demandeur_user_id) ou un nom/prenom/email "
                "pour créer un profil.",
            )
        email = data.demandeur_email.lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                nom=data.demandeur_nom,
                prenom=data.demandeur_prenom,
                hashed_password=hash_password(secrets.token_urlsafe(24)),
                role="client",
                filiale=data.filiale,
                is_active=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

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
        rag_score=pred.get("rag_score"),
        created_at=datetime.now(timezone.utc),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    log_ticket_history(db, ticket.id, admin.id, "statut", None, "En attente (créé par admin)")
    log_ticket_history(db, ticket.id, admin.id, "categorie_finale", None, pred.get("categorie", ""))
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
    query = db.query(Ticket).filter(Ticket.id == ticket_id)
    if user.role != "admin":
        query = query.filter(Ticket.user_id == user.id)
    ticket = query.first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")
    return ticket_to_dict(ticket)


@router.get("/{ticket_id}/similar-titles")
def get_similar_titles(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Titres d'autres tickets déjà résolus sur un problème proche — volontairement
    dépourvu de toute solution technique ou métadonnée IA (score, catégorie brute) :
    le client n'a pas besoin/droit de voir ces détails, juste de savoir qu'il n'est
    pas seul à avoir rencontré ce problème. Réservé au propriétaire du ticket (ou admin).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")
    if ticket.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Accès refusé")

    categorie = ticket.categorie_finale or ticket.categorie_predite or None
    candidates = get_live_candidates(ticket.titre, ticket.description, categorie)
    titres = []
    for c in candidates:
        if c.get("ticket_id") == ticket_id:
            continue
        titre = (c.get("titre") or "").strip()
        if titre and titre not in titres:
            titres.append(titre)
    return {"titres": titres[:3]}


@router.post("/{ticket_id}/feedback")
def submit_feedback(
    ticket_id: int,
    data: FeedbackRequest,
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

    ticket.feedback_vote = data.vote
    ticket.feedback_comment = data.comment or ""
    db.commit()
    db.refresh(ticket)
    return ticket_to_dict(ticket)


@router.patch("/{ticket_id}/approve")
def approve_ticket(
    ticket_id: int,
    body: ApproveRequest,
    background_tasks: BackgroundTasks,
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
    # Un statut inchange n'est pas une "transition" a valider : un ticket deja clos
    # (Resolu/Rejete, sans transition sortante possible) doit rester modifiable
    # (categorie, priorite, classification, solution appliquee...) sans etre bloque
    # par la validation de transition, qui ne s'applique qu'a un vrai changement.
    if new_status != current_status and new_status not in STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            400,
            f"Transition non permise: {current_status} → {new_status}. "
            f"Transitions permises depuis {current_status}: {STATUS_TRANSITIONS.get(current_status, [])}"
        )

    # Cas "nouveau" (aucune correspondance RAG fiable) : la solution appliquée par
    # l'admin devient obligatoire avant de clore le ticket, car c'est elle qui
    # alimentera la base de connaissances pour les prochains tickets similaires.
    if new_status == "Résolu" and (ticket.rag_score is None or ticket.rag_score < NOVELTY_THRESHOLD):
        solution_saisie = (body.commentaire_interne if body.commentaire_interne is not None else ticket.commentaire_admin) or ""
        if not solution_saisie.strip():
            raise HTTPException(
                400,
                "Aucun cas similaire connu pour ce ticket : merci de décrire la solution appliquée "
                "(champ « Solution appliquée ») avant de le marquer comme résolu.",
            )

    # Log du changement de statut
    log_ticket_history(db, ticket.id, admin.id, "statut", ticket.statut, new_status)
    ticket.statut = new_status

    # Priorité finale (corrigée par l'admin si mal évaluée au départ)
    if body.priorite_finale and body.priorite_finale != ticket.priorite_finale:
        log_ticket_history(db, ticket.id, admin.id, "priorite_finale", ticket.priorite_finale, body.priorite_finale)
        ticket.priorite_finale = body.priorite_finale

    # Classification finale (Demande / Incident / Problème / Changement)
    if body.classification_finale and body.classification_finale != ticket.classification_finale:
        log_ticket_history(db, ticket.id, admin.id, "classification_finale", ticket.classification_finale, body.classification_finale)
        ticket.classification_finale = body.classification_finale

    # Assignation — explicite si fournie, sinon auto-assignation a l'admin qui
    # prend le ticket en charge (s'il n'est pas deja assigne a quelqu'un).
    if body.assigne_a:
        if body.assigne_a != ticket.assigne_a:
            log_ticket_history(db, ticket.id, admin.id, "assigne_a", ticket.assigne_a, body.assigne_a)
            ticket.assigne_a = body.assigne_a
    elif new_status == "Prise en Charge" and not ticket.assigne_a:
        nom_admin = f"{admin.prenom} {admin.nom}".strip() or admin.email
        log_ticket_history(db, ticket.id, admin.id, "assigne_a", None, nom_admin)
        ticket.assigne_a = nom_admin

    # Gestion de la catégorie
    previous_category = ticket.categorie_finale or ticket.categorie_predite or ""
    threshold = 0.40
    allow_fallback = not (ticket.confiance is not None and ticket.confiance < threshold)
    
    if body.categorie_finale and body.categorie_finale != previous_category:
        log_ticket_history(db, ticket.id, admin.id, "categorie_finale", previous_category, body.categorie_finale)
        ticket.categorie_finale = body.categorie_finale
        rec = recommend_for_category(
            ticket.titre,
            ticket.description,
            body.categorie_finale,
            allow_fallback=allow_fallback,
        )
        ticket.solution_rag = rec.get("solution", "")
        ticket.knowledge_rag = rec.get("knowledge", "")
        ticket.rag_score = rec.get("rag_score")
        log_ticket_history(db, ticket.id, admin.id, "solution_rag", None, "(mise à jour)")
    elif ticket.confiance is not None and ticket.confiance < threshold:
        rec = recommend_for_category(
            ticket.titre,
            ticket.description,
            ticket.categorie_finale,
            allow_fallback=allow_fallback,
        )
        ticket.solution_rag = rec.get("solution", "")
        ticket.knowledge_rag = rec.get("knowledge", "")
        ticket.rag_score = rec.get("rag_score")
    
    # Commentaires client (réponse IT) — a la prise en charge, un message standard
    # est envoye automatiquement si l'admin n'en a pas saisi un lui-meme.
    if body.commentaire_client or body.commentaire:
        old_comment = ticket.commentaire_client
        new_comment = body.commentaire_client or body.commentaire or ""
        ticket.commentaire_client = new_comment
        log_ticket_history(db, ticket.id, admin.id, "commentaire_client", old_comment, new_comment[:100])
    elif new_status == "Prise en Charge" and not ticket.commentaire_client:
        ticket.commentaire_client = AUTO_MESSAGE_PRISE_EN_CHARGE
        log_ticket_history(db, ticket.id, admin.id, "commentaire_client", None, AUTO_MESSAGE_PRISE_EN_CHARGE)
    elif new_status == "Résolu" and (
        not ticket.commentaire_client or ticket.commentaire_client == AUTO_MESSAGE_PRISE_EN_CHARGE
    ):
        # Le message generique de prise en charge ne doit jamais rester affiche au
        # client une fois le ticket reellement resolu — seul un message explicitement
        # personnalise par l'admin (traite dans le bloc if ci-dessus) le remplace.
        old_comment = ticket.commentaire_client
        ticket.commentaire_client = AUTO_MESSAGE_RESOLU
        log_ticket_history(db, ticket.id, admin.id, "commentaire_client", old_comment, AUTO_MESSAGE_RESOLU)
    
    # Commentaires admin (notes internes)
    if hasattr(ticket, "commentaire_admin"):
        old_admin_comment = ticket.commentaire_admin
        new_admin_comment = body.commentaire_interne or ""
        ticket.commentaire_admin = new_admin_comment
        log_ticket_history(db, ticket.id, admin.id, "commentaire_admin", old_admin_comment, new_admin_comment[:100])
    
    ticket.approved_by = str(admin.id)
    
    # Marquer comme résolu + archiver dans ChromaDB (base de connaissances vectorielle)
    if new_status == "Résolu":
        # resolved_at ne doit etre fixe qu'une seule fois — un admin qui corrige plus
        # tard le texte de sa solution sur un ticket deja resolu ne doit pas voir son
        # "Temps ecoule" repartir de zero.
        if not ticket.resolved_at:
            ticket.resolved_at = datetime.now(timezone.utc)
        # La base de connaissances est alimentée en priorité par la solution
        # reellement appliquee par l'admin (commentaire_admin) — verifiee humainement —
        # et seulement en repli par la suggestion IA d'origine (jamais validee).
        # En tache de fond : le calcul de l'embedding (sentence-transformers) ne doit
        # jamais retarder la reponse HTTP a l'admin qui vient de cliquer "Enregistrer".
        # Re-archive (upsert) aussi sur une correction ulterieure : la base de
        # connaissances doit refleter la derniere version de la solution.
        background_tasks.add_task(
            archive_resolved_ticket,
            ticket_id          = ticket.id,
            titre              = ticket.titre,
            description        = ticket.description,
            categorie          = ticket.categorie_finale or ticket.categorie_predite or "",
            confiance          = ticket.confiance,
            solution           = ticket.commentaire_admin or ticket.solution_rag or "",
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
    ticket.rag_score = rec.get("rag_score")
    log_ticket_history(db, ticket.id, admin.id, "solution_rag", old_solution[:50] if old_solution else None, "(MAJ RAG)")
    db.commit()
    return {
        "message": "RAG mis a jour",
        "id": ticket_id,
        "solution_rag": ticket.solution_rag,
        "knowledge_rag": ticket.knowledge_rag,
        "rag_score": ticket.rag_score,
    }


@router.get("/{ticket_id}/rag-synthesis", response_model=RagSynthesisOut)
def get_rag_synthesis(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Assistant de triage IA (human-in-the-loop) : synthétise les tickets historiques
    similaires (base de connaissances ChromaDB) en français professionnel via un LLM
    local (Ollama), plutôt que d'afficher la résolution brute d'un seul cas.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")

    categorie = ticket.categorie_finale or ticket.categorie_predite or None
    candidates = get_live_candidates(ticket.titre, ticket.description, categorie)
    # Le ticket lui-meme peut apparaitre dans ses propres candidats s'il a deja ete
    # archive (ex : re-analyse apres resolution) — non pertinent pour se comparer a soi-meme.
    candidates = [c for c in candidates if c.get("ticket_id") != ticket_id]
    return synthesize_recommendations(ticket.titre, ticket.description, candidates)


@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Suppression définitive (admin uniquement) — l'historique lié est supprimé
    d'abord pour respecter la contrainte de clé étrangère ticket_history.ticket_id.
    L'éventuelle entrée archivée dans ChromaDB (ticket résolu) est retirée aussi,
    pour ne pas laisser une entrée fantôme réapparaître dans les futures suggestions
    RAG avec un ID de ticket qui n'existe plus."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")

    db.query(TicketHistory).filter(TicketHistory.ticket_id == ticket_id).delete()
    db.delete(ticket)
    db.commit()
    delete_resolved(ticket_id)
    return {"message": "Ticket supprimé", "id": ticket_id}


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


# ── Endpoints base de connaissances vectorielle (ChromaDB) ──────────────────────

@router.get("/resolved/stats")
def get_resolved_stats(_: User = Depends(require_admin)):
    """
    KPIs agrégés des tickets résolus archivés dans ChromaDB.
    Retourne : total, répartition par catégorie, par filiale.
    """
    return vector_stats()


@router.get("/resolved/archive")
def get_resolved_archive(
    limit: int = 50,
    _: User = Depends(require_admin),
):
    """
    Liste des tickets résolus archivés dans ChromaDB (les plus récents en premier).
    Constitue la mémoire institutionnelle des résolutions approuvées.
    """
    docs = get_all_resolved(limit=limit)
    return {"total": len(docs), "tickets": docs}
