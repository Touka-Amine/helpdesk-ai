"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str
    filiale: str = ""


class UserOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: EmailStr
    role: str
    filiale: str = ""
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nom: str
    prenom: str = ""
    user_id: int | None = None
    filiale: str = ""
