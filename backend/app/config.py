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
    # Daily allowances for the actions that call Gemini, now that anyone can sign up
    # (see services/quota.py). Days are UTC.
    daily_new_works_per_user: int = 5
    daily_explanations_per_user: int = 20
    daily_searches_per_user: int = 30
    daily_ai_actions_total: int = 300  # site-wide ceiling across every account and visitor
    signups_per_ip_per_day: int = 3

    model_config = {"env_file": str(_env_file)}


settings = Settings()
