"""Database connection helpers."""

import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings
from api.db.models import Base, User


connect_args = {"check_same_thread": False} if settings.DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialise la base de données : création des tables + migrations + seed."""
    Base.metadata.create_all(bind=engine)
    _migrate_columns()
    _seed_users()


def _migrate_columns() -> None:
    """Ajoute les colonnes manquantes (ALTER TABLE) sans casser la DB existante."""
    if not settings.DB_URL.startswith("sqlite:///"):
        return
    db_path = settings.DB_URL.replace("sqlite:///", "", 1)
    con = sqlite3.connect(db_path)
    existing = {row[1] for row in con.execute("PRAGMA table_info(tickets)").fetchall()}
    expected = {
        "user_id"          : "INTEGER",
        "priorite_saisie"  : "TEXT",
        "filiale"          : "TEXT",
        "equipement"       : "TEXT",
        "commentaire_client": "TEXT",
        "commentaire_admin": "TEXT",
        "feedback_vote"    : "TEXT",
        "feedback_comment" : "TEXT",
        "solution_rag"     : "TEXT",
        "knowledge_rag"    : "TEXT",
        "resolved_at"      : "TEXT",
        "rag_score"        : "REAL",
    }
    for column, column_type in expected.items():
        if column not in existing:
            _add_column_if_missing(con, "tickets", column, column_type)

    existing_users = {row[1] for row in con.execute("PRAGMA table_info(users)").fetchall()}
    expected_users = {
        "first_login": "BOOLEAN DEFAULT 0",
    }
    for column, column_type in expected_users.items():
        if column not in existing_users:
            _add_column_if_missing(con, "users", column, column_type)

    con.commit()
    con.close()


def _add_column_if_missing(con: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    """
    ALTER TABLE tolerant aux courses entre workers uvicorn concurrents (--workers 2) :
    chaque worker relit PRAGMA table_info et ne tente l'ALTER que si la colonne
    manque encore, mais deux workers peuvent passer ce test simultanement avant
    que l'un des deux n'ait commit — le "duplicate column name" resultant est donc
    attendu et ignore plutot que de faire planter le worker au demarrage.
    """
    try:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise


def _seed_users() -> None:
    """
    Crée les utilisateurs de démo et l'utilisateur système s'ils n'existent pas encore.
    Idempotent — vérifie l'existence avant d'insérer.
    Non-fatal : si passlib/bcrypt échoue (incompatibilité de version), on passe.
    """
    try:
        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db = SessionLocal()
        try:
            # Utilisateur système — pour Power Automate / ingest automatique
            # Ne peut pas se connecter (is_active=False)
            if not db.query(User).filter(User.email == "system@helpdesk-ai.local").first():
                db.add(User(
                    email           = "system@helpdesk-ai.local",
                    nom             = "System",
                    prenom          = "Helpdesk",
                    hashed_password = pwd_ctx.hash("no_login_system"),
                    role            = "system",
                    filiale         = "",
                    is_active       = False,
                ))
                db.commit()

            # Utilisateurs de démonstration
            for u in SEED_USERS:
                if not db.query(User).filter(User.email == u["email"]).first():
                    db.add(User(
                        email           = u["email"],
                        nom             = u["nom"],
                        prenom          = u["prenom"],
                        hashed_password = pwd_ctx.hash(u["password"]),
                        role            = u["role"],
                        filiale         = u["filiale"],
                    ))
                    db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Avertissement seeding utilisateurs : {e} — ignoré (DB existante ou bcrypt incompatible)")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SEED_USERS = [
    {
        "email"   : "aminetoukabri@gmail.com",
        "nom"     : "Toukabri",
        "prenom"  : "Amine",
        "password": "client123",
        "role"    : "client",
        "filiale" : "HELIOFLEX",
    },
    {
        "email"   : "mohamedaminetoukabri089@gmail.com",
        "nom"     : "Toukabri",
        "prenom"  : "Mohamed Amine",
        "password": "admin123",
        "role"    : "admin",
        "filiale" : "OTBS",
    },
]
