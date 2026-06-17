# api/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY       : str = "change-this-in-production"
    ALGORITHM        : str = "HS256"
    TOKEN_EXPIRE_MIN : int = 480       # 8 heures
    DB_URL           : str = "sqlite:///./data/tickets.db"
    CONFIDENCE_THRESHOLD : float = 0.40
    ADMIN_EMAILS     : str = ""

    def admin_email_set(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.ADMIN_EMAILS.split(",")
            if email.strip()
        }

    class Config:
        env_file = ".env"

settings = Settings()
