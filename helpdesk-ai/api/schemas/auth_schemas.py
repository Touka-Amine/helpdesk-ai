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
    email: EmailStr
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
    email: EmailStr
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
