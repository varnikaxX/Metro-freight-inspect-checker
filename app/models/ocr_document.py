"""Internal OCR document model.

This model is provider-independent. Everything downstream of the
provider layer (extractors, orchestrator, aggregator) works only with
these types and must never see raw Google Vision SDK objects.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BoundingBoxVertex(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    """A simple normalized bounding polygon."""

    vertices: list[BoundingBoxVertex] = Field(default_factory=list)


class OCRWord(BaseModel):
    text: str
    bounding_box: BoundingBox | None = None
    provider_confidence: float | None = None


class OCRLine(BaseModel):
    text: str
    bounding_box: BoundingBox | None = None
    provider_confidence: float | None = None
    words: list[OCRWord] = Field(default_factory=list)


class OCRDocument(BaseModel):
    """Provider-independent representation of an OCR result for one image."""

    full_text: str = ""
    lines: list[OCRLine] = Field(default_factory=list)
    provider_name: str = "unknown"
    provider_metadata: dict = Field(default_factory=dict)

    @property
    def text_detected(self) -> bool:
        return bool(self.full_text and self.full_text.strip())
