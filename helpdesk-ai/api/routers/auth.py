from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from api.config import settings
from api.db.database import get_db
from api.db.models import User
from api.middleware.auth_middleware import check_login_rate_limit
from api.schemas.auth_schemas import ChangePasswordRequest, TokenOut, UserCreate, UserOut, UserUpdate
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
    if not user or not user.is_active or not verify_password(form.password, user.hashed_password):
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
        "first_login": bool(user.first_login),
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            raise HTTPException(401, "Utilisateur introuvable ou désactivé")
        return user
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Token invalide")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(403, "Acces reserve aux admins")
    return current_user


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.nom is not None:
        user.nom = data.nom
    if data.prenom is not None:
        user.prenom = data.prenom
    if data.filiale is not None:
        user.filiale = data.filiale
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, "Mot de passe actuel incorrect")
    user.hashed_password = hash_password(data.new_password)
    user.first_login = False
    db.commit()
    return {"message": "Mot de passe mis à jour"}
