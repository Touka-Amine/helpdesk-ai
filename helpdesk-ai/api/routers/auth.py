from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from api.config import settings
from api.db.database import get_db
from api.db.models import PasswordReset, User
from api.middleware.auth_middleware import check_login_rate_limit, check_password_reset_rate_limit
from api.schemas.auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageOut,
    ResetPasswordRequest,
    TokenOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from api.services.auth_service import (
    create_token,
    decode_token,
    empreinte_jeton,
    generer_jeton_reinitialisation,
    hash_password,
    verify_password,
)
from api.services.mail_service import envoyer_lien_reinitialisation


router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Reponse unique de /forgot-password, quelle que soit l'existence du compte.
_REPONSE_DEMANDE = (
    "Si un compte est associe a cette adresse, un lien de reinitialisation vient "
    "d'y etre envoye."
)


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email déjà utilisé")

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


# ── Mot de passe oublié ───────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(
    data: ForgotPasswordRequest,
    taches: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(check_password_reset_rate_limit),
):
    """Envoie un lien de réinitialisation à l'adresse indiquée.

    La réponse est identique que l'adresse corresponde ou non à un compte. Un
    message distinct transformerait cet endpoint en annuaire : il suffirait de le
    dérouler sur une liste d'adresses pour savoir qui travaille ici.
    """
    email = data.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if user and user.is_active:
        # Les demandes précédentes encore ouvertes sont fermées : un seul lien
        # valide à la fois, celui que le titulaire vient de demander.
        maintenant = datetime.utcnow()
        (
            db.query(PasswordReset)
            .filter(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
            .update({PasswordReset.used_at: maintenant}, synchronize_session=False)
        )

        jeton_clair, empreinte = generer_jeton_reinitialisation()
        db.add(
            PasswordReset(
                user_id=user.id,
                token_hash=empreinte,
                expires_at=maintenant + timedelta(minutes=settings.RESET_TOKEN_TTL_MIN),
            )
        )
        db.commit()

        lien = (
            f"{settings.APP_BASE_URL.rstrip('/')}"
            f"/auth/reset-password?token={quote(jeton_clair)}"
        )
        # En tâche de fond : la durée d'une connexion SMTP ne doit pas se lire
        # dans le temps de réponse, sinon celui-ci révèle que le compte existe.
        taches.add_task(envoyer_lien_reinitialisation, user.email, lien, user.prenom)

    return {"message": _REPONSE_DEMANDE}


@router.post("/reset-password", response_model=MessageOut)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_password_reset_rate_limit),
):
    """Fixe un nouveau mot de passe à partir du jeton reçu par courriel."""
    demande = (
        db.query(PasswordReset)
        .filter(PasswordReset.token_hash == empreinte_jeton(data.token))
        .first()
    )

    # Un seul message pour les trois refus possibles — jeton inconnu, déjà servi,
    # expiré. Les distinguer renseignerait un tiers sur l'état d'un lien intercepté.
    if (
        demande is None
        or demande.used_at is not None
        or demande.expires_at < datetime.utcnow()
    ):
        raise HTTPException(400, "Lien invalide ou expiré. Refaites une demande.")

    user = db.query(User).filter(User.id == demande.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(400, "Lien invalide ou expiré. Refaites une demande.")

    user.hashed_password = hash_password(data.new_password)
    # Le compte a prouvé qu'il maîtrise sa boîte : le passage obligé par l'écran
    # de premier mot de passe n'a plus d'objet.
    user.first_login = False
    demande.used_at = datetime.utcnow()
    db.commit()

    return {"message": "Mot de passe mis à jour. Vous pouvez vous connecter."}
