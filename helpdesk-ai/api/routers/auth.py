from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from api.config import settings
from api.db.database import get_db
from api.db.models import User
from api.middleware.auth_middleware import check_login_rate_limit
from api.schemas.auth_schemas import TokenOut, UserCreate, UserOut
from api.services.auth_service import create_token, decode_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email deja utilise")

    role = "admin" if email in settings.admin_email_set() else "client"
    user = User(
        email=email,
        nom=data.nom,
        prenom=data.prenom,
        hashed_password=hash_password(data.password),
        role=role,
        filiale=data.filiale,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(check_login_rate_limit),
):
    email = form.username.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Identifiants incorrects")

    token = create_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "nom": user.nom,
        "prenom": user.prenom,
        "user_id": user.id,
        "filiale": user.filiale or "",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(401, "Utilisateur introuvable")
        return user
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Token invalide")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(403, "Acces reserve aux admins")
    return current_user
