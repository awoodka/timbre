from pathlib import Path

from pydantic_settings import BaseSettings

# Look for .env in project root (one level up from backend/)
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mediafingerprint:mediafingerprint@localhost:5432/mediafingerprint"
    gemini_api_key: str = ""
    tmdb_api_key: str = ""  # The Movie Database — film/TV metadata + posters
    rawg_api_key: str = ""  # RAWG — video game metadata + covers
    # Enable TLS to Postgres. Off for local Docker; on for managed Postgres
    # (RDS / Supabase / Neon) which require SSL. Driven by the DB_SSL env var.
    db_ssl: bool = False
    # Auth: secret for signing JWT session cookies (override in prod via SECRET_KEY)
    secret_key: str = "dev-insecure-change-me-in-production"
    # HTTPS-only session cookies. False for local http dev; set COOKIE_SECURE=true in
    # prod (behind the tunnel's TLS) so the cookie is never sent over plain http.
    cookie_secure: bool = False
    access_token_ttl_days: int = 30

    model_config = {"env_file": str(_env_file)}


settings = Settings()
