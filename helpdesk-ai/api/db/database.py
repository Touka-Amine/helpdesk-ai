"""Database connection helpers."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from api.config import settings
from api.db.models import Base, User


connect_args = {"check_same_thread": False} if settings.DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialise la base de données : création des tables + migrations + seed."""
    _create_tables()
    _migrate_columns()
    _seed_users()


def _create_tables() -> None:
    """
    Base.metadata.create_all() tolerant aux courses entre workers uvicorn concurrents
    (--workers 2) : sous PostgreSQL, deux workers demarrant simultanement sur une base
    neuve peuvent tous deux constater qu'une table n'existe pas encore et tenter sa
    creation (avec la sequence SERIAL associee) — le perdant echoue alors sur une
    contrainte d'unicite deja posee par l'autre. Meme classe de course que
    _add_column_if_missing() ci-dessous, a l'etape CREATE TABLE plutot que ALTER TABLE.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        msg = str(e).lower()
        if "already exists" not in msg and "duplicate key" not in msg:
            raise


def _migrate_columns() -> None:
    """Ajoute les colonnes manquantes (ALTER TABLE) — compatible SQLite et PostgreSQL."""
    inspector = inspect(engine)

    expected_tickets = {
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
        "priorite_finale"  : "TEXT",
        "classification_finale": "TEXT",
        "assigne_a"        : "TEXT",
    }
    _sync_columns(inspector, "tickets", expected_tickets)

    expected_users = {
        "first_login": "BOOLEAN DEFAULT FALSE",
    }
    _sync_columns(inspector, "users", expected_users)


def _sync_columns(inspector, table: str, expected: dict[str, str]) -> None:
    existing = {col["name"] for col in inspector.get_columns(table)}
    for column, column_type in expected.items():
        if column not in existing:
            _add_column_if_missing(table, column, column_type)


def _add_column_if_missing(table: str, column: str, column_type: str) -> None:
    """
    ALTER TABLE tolerant aux courses entre workers uvicorn concurrents (--workers 2) :
    chaque worker relit les colonnes existantes et ne tente l'ALTER que si la colonne
    manque encore, mais deux workers peuvent passer ce test simultanement avant que l'un
    des deux n'ait commit — l'erreur "colonne deja existante" resultante (SQLite comme
    PostgreSQL, formulations differentes) est donc attendue et ignoree plutot que de
    faire planter le worker au demarrage.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
    except Exception as e:
        msg = str(e).lower()
        if "duplicate column" not in msg and "already exists" not in msg:
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
