# api/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY           : str   = "change-this-in-production-min-32-chars"
    ALGORITHM            : str   = "HS256"
    TOKEN_EXPIRE_MIN     : int   = 480
    DB_URL               : str   = "sqlite:///./data/tickets.db"
    CONFIDENCE_THRESHOLD : float = 0.40
    ADMIN_EMAILS         : str   = ""
    CORS_ORIGINS         : str   = "http://localhost:4200,http://localhost:3000"
    INGEST_API_KEY       : str   = "change-this-api-key-for-power-automate"

    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
