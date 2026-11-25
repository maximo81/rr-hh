"""Configuración leída desde variables de entorno / archivo .env (nunca hardcodear secretos)."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env", extra="ignore"
    )


settings = Settings()
