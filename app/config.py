"""Application configuration.

Loads configuration from environment variables (and an optional .env
file). Never hardcode credentials here.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the OCR service."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Maximum number of images accepted in a single scan request.
    max_images: int = 5

    # Timeout (seconds) applied to each image download.
    image_download_timeout: int = 15

    # Maximum allowed size (in MB) for a single downloaded image.
    max_image_size_mb: int = 10

    # Standard Google credential env var. The Google client library reads
    # this itself; it is declared here only so it surfaces in Settings.
    google_application_credentials: str | None = None

    app_name: str = "OCR Service"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
