"""Routes admin : gestion des utilisateurs + informations modèle."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import User
from api.routers.auth import require_admin
from api.schemas.auth_schemas import AdminUserCreate, AdminUserCreateOut, AdminUserOut, AdminUserUpdate
from api.services.auth_service import generate_temp_password, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

MODEL_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "model_metadata.json"


@router.get("/health")
def admin_health() -> dict:
    return {"status": "ok", "module": "admin"}


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).filter(User.role != "system").order_by(User.id.desc()).all()


@router.post("/users", response_model=AdminUserCreateOut)
def create_user(
    data: AdminUserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email deja utilise")

    temp_password = generate_temp_password()
    user = User(
        email=email,
        nom=data.nom,
        prenom=data.prenom,
        hashed_password=hash_password(temp_password),
        role=data.role,
        filiale=data.filiale,
        is_active=True,
        first_login=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": user, "temp_password": temp_password}


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    if user.id == admin.id and data.is_active is False:
        raise HTTPException(400, "Impossible de désactiver son propre compte")

    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/model-info")
def model_info(_: User = Depends(require_admin)):
    """Métriques réelles du modèle ML entraîné (models/model_metadata.json)."""
    if not MODEL_METADATA_PATH.exists():
        raise HTTPException(404, "model_metadata.json introuvable")
    with open(MODEL_METADATA_PATH, encoding="utf-8") as f:
        return json.load(f)
