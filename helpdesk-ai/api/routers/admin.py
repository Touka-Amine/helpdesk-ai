"""
Routes admin : gestion des utilisateurs, informations modèle, MLOps.

Les routes MLOps sont en LECTURE SEULE, à une exception près : le rechargement du
modèle servi. Aucune ne lance d'entraînement ni ne promeut de modèle. Entraîner et
promouvoir passent par le pipeline DVC, hors de l'API, pour que ces opérations
restent tracées, reproductibles et déclenchées volontairement.
"""

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

_RACINE = Path(__file__).resolve().parents[2]
MODEL_METADATA_PATH = _RACINE / "models" / "model_metadata.json"
REGISTRY_INDEX_PATH = _RACINE / "models" / "registry" / "registry.json"
METRICS_DIR = _RACINE / "metrics"


def _lire_json(chemin: Path, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return defaut


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
    # Profil : un nom fait d'espaces seulement ne remplace pas le nom existant.
    for champ in ("nom", "prenom"):
        valeur = getattr(data, champ)
        if valeur is not None:
            valeur = valeur.strip()
            if not valeur:
                raise HTTPException(422, f"Le champ {champ} ne peut pas être vide")
            setattr(user, champ, valeur)
    if data.filiale is not None:
        user.filiale = data.filiale.strip()
    db.commit()
    db.refresh(user)
    return user


# Pas de route pour changer le mot de passe d'un autre compte, volontairement :
# chacun change le sien (POST /auth/change-password), et un mot de passe oublie
# passe par le lien envoye a son titulaire (POST /auth/forgot-password). Un
# administrateur ne peut donc jamais connaitre ni choisir le mot de passe d'un
# autre utilisateur, hormis le mot de passe provisoire d'un compte qu'il cree.


@router.get("/model-info")
def model_info(_: User = Depends(require_admin)):
    """Métriques réelles du modèle ML entraîné (models/model_metadata.json)."""
    if not MODEL_METADATA_PATH.exists():
        raise HTTPException(404, "model_metadata.json introuvable")
    with open(MODEL_METADATA_PATH, encoding="utf-8") as f:
        metadata = json.load(f)
    from api.predictor import predictor
    metadata["_service"] = predictor.info()
    return metadata


# ── MLOps — axe 1 : cycle de vie du modèle ───────────────────────────────────

@router.get("/registry")
def registry(_: User = Depends(require_admin)):
    """
    Registre des modèles : versions, alias de production, historique des décisions.

    Répond aux questions de traçabilité : quel modèle est en production, sur quel
    dataset il a été entraîné, quelles métriques il a obtenues, et pourquoi chaque
    candidat a été accepté ou rejeté.
    """
    index = _lire_json(REGISTRY_INDEX_PATH)
    if index is None:
        return {
            "disponible": False,
            "motif": "Aucun registre. Il est créé au premier `python src/pipeline/train.py`.",
            "versions": [], "aliases": {}, "history": [],
        }
    index["disponible"] = True
    index["versions"] = sorted(index.get("versions", []),
                               key=lambda v: v["version"], reverse=True)
    index["history"] = index.get("history", [])[-50:]
    return index


@router.get("/promotion-decision")
def promotion_decision(_: User = Depends(require_admin)):
    """Dernière décision de promotion, porte par porte, avec son motif."""
    decision = _lire_json(METRICS_DIR / "promotion_decision.json")
    if decision is None:
        return {"disponible": False,
                "motif": "Aucune décision enregistrée. Lancez `python src/pipeline/promote.py`."}
    return decision


@router.post("/model/reload")
def model_reload(_: User = Depends(require_admin)):
    """
    Recharge le modèle servi depuis le disque, après une promotion ou un rollback.

    Ne change PAS quelle version est en production : cela relève du registre. Cette
    route ne fait qu'appliquer la décision déjà prise, sans redémarrer le conteneur.

    Avec plusieurs workers uvicorn, cet appel n'atteint que le worker qui le traite.
    Les autres se rechargent seuls dans les trente secondes en comparant le pointeur
    du registre au modèle qu'ils ont en mémoire (api/predictor.py, ensure_fresh).
    """
    from api.predictor import predictor
    avant = predictor.model_version
    try:
        apres = predictor.reload()
    except Exception as exc:
        raise HTTPException(500, f"Rechargement impossible : {type(exc).__name__}: {exc}")
    return {
        "recharge": True,
        "version_avant": avant,
        "version_apres": apres,
        "note": ("Les autres workers appliqueront le changement dans les 30 secondes."
                 if avant != apres else "Le worker servait déjà cette version."),
        "service": predictor.info(),
    }


# ── Monitoring — lecture des rapports produits hors ligne ────────────────────

@router.get("/monitoring/ml")
def monitoring_ml(_: User = Depends(require_admin)):
    """Rapport de src/monitoring/ml_monitor.py. Généré hors ligne, jamais calculé ici."""
    rapport = _lire_json(METRICS_DIR / "ml_monitor.json")
    if rapport is None:
        return {"disponible": False,
                "motif": "Aucun rapport. Lancez `python src/monitoring/ml_monitor.py`."}
    return rapport


@router.get("/monitoring/rag")
def monitoring_rag(_: User = Depends(require_admin)):
    """Rapport de src/monitoring/rag_monitor.py."""
    rapport = _lire_json(METRICS_DIR / "rag_monitor.json")
    if rapport is None:
        return {"disponible": False,
                "motif": "Aucun rapport. Lancez `python src/monitoring/rag_monitor.py`."}
    return rapport


@router.get("/monitoring/retrain-trigger")
def retrain_trigger(_: User = Depends(require_admin)):
    """
    État des déclencheurs de réentraînement.

    Recommandation, jamais action. Aucun endpoint de cette API ne lance un
    entraînement : c'est une décision humaine, exécutée par `dvc repro`.
    """
    trigger = _lire_json(METRICS_DIR / "should_retrain.json")
    if trigger is None:
        return {"disponible": False, "should_retrain": False,
                "motif": "Aucune évaluation. Lancez `python src/monitoring/ml_monitor.py`."}
    return trigger


@router.get("/monitoring/rag-eval")
def rag_eval(_: User = Depends(require_admin)):
    """Dernière évaluation hors ligne de la qualité de récupération du RAG."""
    rapport = _lire_json(METRICS_DIR / "rag_eval.json")
    if rapport is None:
        return {"disponible": False,
                "motif": "Aucune évaluation. Lancez `python src/pipeline/rag_eval.py`."}
    return rapport
