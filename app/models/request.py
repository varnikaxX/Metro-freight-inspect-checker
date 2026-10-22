"""Request models for the /ocr/scan endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.config import get_settings


class ImageInput(BaseModel):
    """A single image to be processed as part of a scan."""

    image_id: str = Field(..., min_length=1, description="Caller-supplied identifier for this image.")
    image_url: HttpUrl = Field(..., description="Publicly accessible URL of the image.")


class ScanRequest(BaseModel):
    """Request body for POST /ocr/scan."""

    scan_id: str = Field(..., min_length=1)
    images: list[ImageInput] = Field(..., min_length=1)

    @field_validator("images")
    @classmethod
    def validate_max_images(cls, images: list[ImageInput]) -> list[ImageInput]:
        max_images = get_settings().max_images
        if len(images) > max_images:
            raise ValueError(f"A maximum of {max_images} images is allowed per scan request.")
        return images
