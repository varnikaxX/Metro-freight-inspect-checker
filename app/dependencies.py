"""FastAPI dependency wiring.

Kept intentionally simple: plain functions used with Depends(). Tests
override get_ocr_provider (and get_image_service) with fakes via
app.dependency_overrides, so no real Google credentials or network
access are ever required to run the test suite.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.providers.base import OCRProvider
from app.providers.google_vision import GoogleVisionProvider
from app.services.image_service import ImageService
from app.services.orchestrator import OCROrchestrator


@lru_cache
def get_ocr_provider() -> OCRProvider:
    """Return the OCR provider to use. Overridden in tests."""
    return GoogleVisionProvider()


def get_image_service(settings: Settings = Depends(get_settings)) -> ImageService:
    return ImageService(settings)


def get_orchestrator(
    provider: OCRProvider = Depends(get_ocr_provider),
    image_service: ImageService = Depends(get_image_service),
) -> OCROrchestrator:
    return OCROrchestrator(provider=provider, image_service=image_service)
