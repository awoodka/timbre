from pathlib import Path

from pydantic_settings import BaseSettings

# Look for .env in project root (one level up from backend/)
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mediafingerprint:mediafingerprint@localhost:5432/mediafingerprint"
    gemini_api_key: str = ""

    model_config = {"env_file": str(_env_file)}


settings = Settings()
