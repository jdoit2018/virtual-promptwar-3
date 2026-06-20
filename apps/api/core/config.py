"""
apps/api/core/config.py
Application settings loaded from environment variables via pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Resolve root .env.local regardless of where uvicorn is invoked from
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env.local"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    NODE_ENV: str = "development"
    CRON_SECRET: str = "change-me"

    # Database
    DATABASE_URL: str = "postgresql://carbon_user:carbon_pass@localhost:5432/carbon_db"

    # Firebase Admin
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_PRIVATE_KEY: str = ""

    # Google APIs
    GOOGLE_MAPS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GOOGLE_CLOUD_PROJECT: str = ""
    GCS_BUCKET_AVATARS: str = ""
    GCS_BUCKET_EXPORTS: str = ""

    # External
    CLIMATIQ_API_KEY: str = ""

    # CORS — comma-separated origins
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return ["http://localhost:3000", "https://yourdomain.com"]


settings = Settings()
