from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="client")
    filiale = Column(String, default="")
    is_active = Column(Boolean, default=True)
    first_login = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("Ticket", back_populates="user", foreign_keys="Ticket.user_id")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(String, nullable=True)
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priorite_saisie = Column(String, default="Modere")
    priorite_finale = Column(String, nullable=True)
    classification_finale = Column(String, nullable=True)
    assigne_a = Column(String, nullable=True)
    filiale = Column(String, default="")
    equipement = Column(String, default="")
    categorie_predite = Column(String)
    categorie_finale = Column(String)
    confiance = Column(Float)
    statut = Column(String, default="En attente")
    solution_rag = Column(Text, default="")
    knowledge_rag = Column(Text, default="")
    rag_score = Column(Float, nullable=True)
    commentaire_client = Column(Text, default="")
    commentaire_admin = Column(Text, default="")
    feedback_vote = Column(String, nullable=True)
    feedback_comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # ── Tracabilite de la prediction (MLOps, axe 1) ────────────────────────────
    # Ces trois champs ne se reconstruisent pas apres coup : un ticket cree sans
    # eux est definitivement perdu pour le monitoring. Ils repondent aux questions
    # "quel modele a produit cette categorie" et "une regle metier l'a-t-elle
    # ecrasee", que src/monitoring/ml_monitor.py exploite.
    model_version = Column(String, nullable=True)
    heuristic_applied = Column(Boolean, default=False)
    heuristic_rule = Column(String, nullable=True)

    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    history = relationship("TicketHistory", back_populates="ticket")


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    champ_modifie = Column(String)
    ancienne_valeur = Column(Text)
    nouvelle_valeur = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="history")
