# api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore" : le fichier .env est partagé avec docker-compose, qui y lit
    # POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB pour le service postgres. Sans
    # cette tolérance, pydantic-settings refuse de construire Settings à cause de ces
    # trois clés, et toute importation de api.main échoue — ce qui rendait
    # tests/test_api_integration.py incollectable en local.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    # "development" (defaut) ou "production". En production, le service refuse de
    # demarrer si un secret est reste a sa valeur d'exemple : le fichier .env.example
    # est public, et le copier tel quel mettrait en service des secrets connus de
    # quiconque lit le depot. Risque R-09 du registre.
    ENVIRONMENT          : str   = "development"

    # ── Messagerie sortante (reinitialisation de mot de passe) ────────────────
    # SMTP_HOST vide = messagerie desactivee. Le parcours "mot de passe oublie"
    # reste alors fonctionnel cote API, mais aucun courriel ne part : hors
    # production le lien est ecrit dans le journal du service pour permettre les
    # essais, jamais en production.
    SMTP_HOST            : str   = ""
    SMTP_PORT            : int   = 587
    SMTP_USER            : str   = ""
    SMTP_PASSWORD        : str   = ""
    SMTP_FROM            : str   = "no-reply@onetech-bs.com"
    SMTP_STARTTLS        : bool  = True
    SMTP_TIMEOUT         : float = 15.0
    # Base de l'URL du frontend, utilisee pour construire le lien envoye par courriel.
    APP_BASE_URL         : str   = "http://localhost:4200"
    # Duree de validite du lien de reinitialisation, en minutes.
    RESET_TOKEN_TTL_MIN  : int   = 30

    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def messagerie_configuree(self) -> bool:
        """Vrai si un serveur SMTP est renseigne, donc si un courriel peut partir."""
        return bool(self.SMTP_HOST.strip())

    def secrets_non_configures(self) -> list[str]:
        """Noms des secrets encore a leur valeur d'exemple, sans jamais les exposer."""
        suspects = {
            "SECRET_KEY": self.SECRET_KEY,
            "INGEST_API_KEY": self.INGEST_API_KEY,
            "DB_URL": self.DB_URL,
        }
        # Le mot de passe SMTP n'est un secret attendu que si la messagerie sert.
        if self.messagerie_configuree():
            suspects["SMTP_PASSWORD"] = self.SMTP_PASSWORD
        marqueurs = ("change-this", "REMPLACER__", "helpdesk:helpdesk")
        return [nom for nom, valeur in suspects.items()
                if any(m in valeur for m in marqueurs)]

    def verifier_secrets(self) -> None:
        """Interrompt le demarrage en production si un secret n'a pas ete genere."""
        if self.ENVIRONMENT.strip().lower() != "production":
            return
        manquants = self.secrets_non_configures()
        if manquants:
            raise RuntimeError(
                "Secrets encore a leur valeur d'exemple : "
                + ", ".join(manquants)
                + ". Generer une valeur par cle avant tout demarrage en production "
                  "(python -c \"import secrets; print(secrets.token_urlsafe(48))\")."
            )


settings = Settings()
