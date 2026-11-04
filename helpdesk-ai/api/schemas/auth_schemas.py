"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str
    filiale: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    # Adresse relue en base, pas revalidee : voir la note sur AdminUserOut.
    email: str
    role: str
    filiale: str = ""
    created_at: datetime | None = None


class UserUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    filiale: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=6)


class MessageOut(BaseModel):
    message: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nom: str
    prenom: str = ""
    user_id: int | None = None
    filiale: str = ""
    first_login: bool = False


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    # Type `str` et non `EmailStr`, volontairement.
    #
    # Revalider une adresse en sortie n'apporte rien : elle a deja ete verifiee
    # a la creation du compte. En revanche, FastAPI valide chaque ligne avant
    # d'envoyer la reponse, donc une seule adresse jugee invalide fait echouer
    # la liste entiere et l'ecran n'affiche plus personne. C'est arrive avec des
    # comptes de test ecrits directement en base sur un domaine reserve (.local),
    # que le validateur d'adresses refuse. Les schemas d'entree, eux, gardent
    # `EmailStr` : c'est la que la verification a un sens.
    email: str
    role: str
    filiale: str = ""
    is_active: bool = True
    first_login: bool = False
    created_at: datetime | None = None


class AdminUserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    role: str = Field(..., pattern="^(admin|client)$")
    filiale: str = ""


class AdminUserCreateOut(BaseModel):
    user: AdminUserOut
    temp_password: str


class AdminUserUpdate(BaseModel):
    role: str | None = Field(None, pattern="^(admin|client)$")
    is_active: bool | None = None
    # Profil. L'adresse n'est pas modifiable ici : c'est l'identifiant de
    # connexion, et la changer sans verification ouvrirait la porte a un
    # detournement de compte.
    nom: str | None = Field(None, min_length=1, max_length=100)
    prenom: str | None = Field(None, min_length=1, max_length=100)
    filiale: str | None = Field(None, max_length=50)
