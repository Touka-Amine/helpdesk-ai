# api/services/auth_service.py
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