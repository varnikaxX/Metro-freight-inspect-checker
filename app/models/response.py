"""Response models for the /ocr/scan endpoint.

These models define the stable API contract returned to the main
backend / rule engine.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.ocr_document import BoundingBox


class ScanStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ImageStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class FieldStatus(str, Enum):
    NOT_FOUND = "not_found"
    FOUND = "found"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    CONFLICT = "conflict"  # <-- Ensure this exists


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    IMAGE_DOWNLOAD_FAILED = "IMAGE_DOWNLOAD_FAILED"
    INVALID_IMAGE = "INVALID_IMAGE"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    OCR_PROVIDER_UNAVAILABLE = "OCR_PROVIDER_UNAVAILABLE"
    OCR_PROVIDER_ERROR = "OCR_PROVIDER_ERROR"
    OCR_PROCESSING_FAILED = "OCR_PROCESSING_FAILED"


class ScanError(BaseModel):
    image_id: str | None = None
    code: ErrorCode
    message: str


class ImageResult(BaseModel):
    image_id: str
    status: ImageStatus
    text_detected: bool = False
    raw_text: str | None = None
    error: ScanError | None = None


# ---------------------------------------------------------------------------
# Field candidates
# ---------------------------------------------------------------------------


class MRPCandidate(BaseModel):
    raw_text: str
    normalized_value: float | None = None
    currency: str | None = "INR"
    confidence: Confidence
    source_image_id: str
    bounding_box: BoundingBox | None = None


class NetQuantityCandidate(BaseModel):
    raw_text: str
    value: float | None = None
    unit: str | None = None
    confidence: Confidence
    source_image_id: str
    bounding_box: BoundingBox | None = None


class DateDeclarationCandidate(BaseModel):
    label: str
    raw_value: str
    normalized_value: str | None = None
    declaration_type: str | None = None
    confidence: Confidence
    source_image_id: str
    bounding_box: BoundingBox | None = None


class ManufacturerCandidate(BaseModel):
    label: str
    raw_text: str
    confidence: Confidence
    source_image_id: str
    bounding_box: BoundingBox | None = None


class MRPFieldResult(BaseModel):
    status: FieldStatus
    candidates: list[MRPCandidate] = Field(default_factory=list)


class NetQuantityFieldResult(BaseModel):
    status: FieldStatus
    candidates: list[NetQuantityCandidate] = Field(default_factory=list)


class DateDeclarationsFieldResult(BaseModel):
    status: FieldStatus
    candidates: list[DateDeclarationCandidate] = Field(default_factory=list)


class ManufacturerFieldResult(BaseModel):
    status: FieldStatus
    candidates: list[ManufacturerCandidate] = Field(default_factory=list)


class Fields(BaseModel):
    mrp: MRPFieldResult
    net_quantity: NetQuantityFieldResult
    date_declarations: DateDeclarationsFieldResult
    manufacturer_declarations: ManufacturerFieldResult


class ScanSummary(BaseModel):
    images_received: int
    images_processed: int
    images_failed: int


class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    summary: ScanSummary
    images: list[ImageResult]
    fields: Fields
    errors: list[ScanError] = Field(default_factory=list)
