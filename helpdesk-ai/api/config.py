# api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    SECRET_KEY           : str   = "change-this-in-production-min-32-chars"
    ALGORITHM            : str   = "HS256"
    TOKEN_EXPIRE_MIN     : int   = 480
    # Par défaut : service "postgres" du docker-compose. Pour un lancement hors Docker,
    # surcharger via .env (ex: postgresql+psycopg2://user:pass@localhost:5432/helpdesk,
    # ou revenir à sqlite:///./data/tickets.db pour un dev local sans serveur Postgres).
    DB_URL               : str   = "postgresql+psycopg2://helpdesk:helpdesk@postgres:5432/helpdesk"
    CONFIDENCE_THRESHOLD : float = 0.40
    ADMIN_EMAILS         : str   = ""
    CORS_ORIGINS         : str   = "http://localhost:4200,http://localhost:3000"
    INGEST_API_KEY       : str   = "change-this-api-key-for-power-automate"
    # LLM local (Ollama) — synthese "human-in-the-loop" des tickets similaires (RAG admin).
    # Par defaut : service "ollama" du docker-compose. Hors Docker : http://localhost:11434.
    OLLAMA_HOST          : str   = "http://ollama:11434"
    OLLAMA_MODEL         : str   = "llama3.2:3b"
    OLLAMA_TIMEOUT       : float = 90.0

    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
