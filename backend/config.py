"""
config.py
---------
Centralised environment configuration for the Legal Metrology Compliance
Verification backend (ID26034). Loads values from a `.env` file (or the
real process environment in production) using pydantic-settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # --- Supabase ---------------------------------------------------------
    SUPABASE_URL: str
    SUPABASE_KEY: str  # service_role key (server-side only, never expose to client)
    SUPABASE_BUCKET_RAW: str = "raw-labels"

    # --- OCR (local Tesseract or Google Cloud Vision) ----------------------
    # OCR_ENGINE: "tesseract" for local Tesseract only, or "google_vision" (default) for Google Cloud Vision with Tesseract fallback.
    OCR_ENGINE: str = "google_vision"
    # Full path to tesseract.exe if it's not on PATH.
    # e.g. C:\Program Files\Tesseract-OCR\tesseract.exe
    TESSERACT_CMD: str = ""

    # --- OCR.space (legacy, optional — no longer used by default) ---
    OCR_SPACE_API_KEY: str = "helloworld"

    # --- Google Cloud Vision (credentials via GOOGLE_APPLICATION_CREDENTIALS env var) ---
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    OCR_LANGUAGE: str = "eng"
    DEBUG_OCR: bool = False

    # --- App ----------------------------------------------------------------
    APP_NAME: str = "Legal Metrology Compliance Verification API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ALLOW_ORIGINS: str = "*"  # comma-separated list, or "*" for all

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the .env file is parsed only once."""
    return Settings()


settings = get_settings()