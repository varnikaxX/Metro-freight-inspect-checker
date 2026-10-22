"""OCR provider interface.

All OCR providers must implement this interface and return the internal
OCRDocument model. No provider-specific SDK objects may leak past this
boundary.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.ocr_document import OCRDocument


class OCRProviderError(Exception):
    """Base class for controlled provider errors."""


class OCRProviderUnavailableError(OCRProviderError):
    """Raised when the provider cannot be reached (network/auth/quota)."""


class OCRProviderProcessingError(OCRProviderError):
    """Raised when the provider was reached but failed to process the image."""


class OCRProvider(ABC):
    """Abstract interface implemented by every OCR provider."""

    @abstractmethod
    def detect_text(self, image_bytes: bytes) -> OCRDocument:
        """Run OCR on the given image bytes and return an OCRDocument.

        Implementations must translate provider-specific exceptions into
        OCRProviderUnavailableError or OCRProviderProcessingError. Raw
        SDK exceptions must never propagate past this method.
        """
        raise NotImplementedError
