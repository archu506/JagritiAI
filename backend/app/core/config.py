from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "JagritiAI"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://jagriti:jagriti@localhost:5432/jagriti_db"

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    GEMINI_API_KEY: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    MAPS_API_KEY: Optional[str] = None

    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: list[str] = ["en", "hi", "or"]

    K_ANONYMITY_THRESHOLD: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
