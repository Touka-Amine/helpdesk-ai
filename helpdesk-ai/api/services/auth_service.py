# api/services/auth_service.py
import hashlib
import secrets
import string

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from api.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def generate_temp_password() -> str:
    """Génère un mot de passe temporaire lisible, ex. 'Xhq@4821'."""
    prefix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(3)).capitalize()
    digits = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"{prefix}@{digits}"

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.TOKEN_EXPIRE_MIN
    )
    return jwt.encode(payload, settings.SECRET_KEY,
                      algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY,
                      algorithms=[settings.ALGORITHM])


# ── Reinitialisation de mot de passe ──────────────────────────────────────────

def empreinte_jeton(jeton_clair: str) -> str:
    """Empreinte SHA-256 du jeton, seule forme conservee en base.

    SHA-256 et non bcrypt : le jeton fait 64 caracteres tires au hasard, il n'a
    donc pas besoin d'etre ralenti contre une attaque par dictionnaire, et la
    verification doit rester immediate a chaque clic sur le lien.
    """
    return hashlib.sha256(jeton_clair.encode("utf-8")).hexdigest()


def generer_jeton_reinitialisation() -> tuple[str, str]:
    """Renvoie le couple (jeton en clair a envoyer, empreinte a stocker)."""
    jeton_clair = secrets.token_urlsafe(48)
    return jeton_clair, empreinte_jeton(jeton_clair)