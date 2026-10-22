"""Image download and validation service."""
from __future__ import annotations

import io
import logging

import httpx
from PIL import Image, UnidentifiedImageError

from app.config import Settings

logger = logging.getLogger(__name__)


class ImageDownloadError(Exception):
    """Raised when an image cannot be downloaded."""


class ImageTooLargeError(Exception):
    """Raised when a downloaded image exceeds the configured size limit."""


class InvalidImageError(Exception):
    """Raised when downloaded bytes do not represent a readable image."""


class ImageService:
    """Downloads and validates images referenced by URL.

    Intentionally minimal: no blur/brightness scoring, no deskewing, no
    enhancement. The original image bytes are passed straight to the OCR
    provider.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_and_validate(self, image_url: str) -> bytes:
        """Download an image and validate it. Returns raw image bytes."""
        image_bytes = self._download(image_url)
        self._validate_size(image_bytes)
        self._validate_readable(image_bytes)
        return image_bytes

    def _download(self, image_url: str) -> bytes:
        timeout = self._settings.image_download_timeout
        max_bytes = self._settings.max_image_size_mb * 1024 * 1024

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                with client.stream("GET", image_url) as response:
                    response.raise_for_status()

                    image_bytes = bytearray()
                    for chunk in response.iter_bytes(chunk_size=8192):
                        image_bytes.extend(chunk)
                        if len(image_bytes) > max_bytes:
                            raise ImageTooLargeError(
                                f"Image exceeds maximum allowed size of {self._settings.max_image_size_mb}MB."
                            )
                    return bytes(image_bytes)

        except httpx.TimeoutException as exc:
            raise ImageDownloadError(f"Timed out downloading image after {timeout}s.") from exc
        except httpx.HTTPStatusError as exc:
            raise ImageDownloadError(
                f"Image download failed with status {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise ImageDownloadError(f"Image download failed: {exc}") from exc

    def _validate_size(self, image_bytes: bytes) -> None:
        max_bytes = self._settings.max_image_size_mb * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise ImageTooLargeError(
                f"Image size {len(image_bytes)} bytes exceeds limit of {max_bytes} bytes."
            )

    def _validate_readable(self, image_bytes: bytes) -> None:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError(f"Downloaded content is not a readable image: {exc}") from exc