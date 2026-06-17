"""Database connection helpers."""

import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings
from api.db.models import Base


connect_args = {"check_same_thread": False} if settings.DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.DB_URL.startswith("sqlite:///"):
        db_path = settings.DB_URL.replace("sqlite:///", "", 1)
        con = sqlite3.connect(db_path)
        existing = {row[1] for row in con.execute("PRAGMA table_info(tickets)").fetchall()}
        expected = {
            "user_id": "INTEGER",
            "priorite_saisie": "TEXT",
            "filiale": "TEXT",
            "equipement": "TEXT",
            "commentaire_client": "TEXT",
            "commentaire_admin": "TEXT",
            "solution_rag": "TEXT",
            "knowledge_rag": "TEXT",
            "resolved_at": "TEXT",
        }
        for column, column_type in expected.items():
            if column not in existing:
                con.execute(f"ALTER TABLE tickets ADD COLUMN {column} {column_type}")
        con.commit()
        con.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SEED_USERS = [
    {
        "email"    : "aminetoukabri@gmail.com",
        "nom"      : "Toukabri",
        "prenom"   : "Amine",
        "password" : "client123",
        "role"     : "client",
        "filiale"  : "HELIOFLEX"
    },
    {
        "email"    : "mohamedaminetoukabri089@gmail.com",
        "nom"      : "Toukabri",
        "prenom"   : "Mohamed Amine",
        "password" : "admin123",
        "role"     : "admin",          # ← rôle admin
        "filiale"  : "OTBS"
    }
]