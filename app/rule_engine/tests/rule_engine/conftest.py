"""Shared fixtures for Rule Engine tests.

Builds realistic ScanResponse objects using the ACTUAL existing OCR
models from app.models.response, per project instructions -- no
alternate/invented OCR response object is used anywhere in these tests.
"""
from __future__ import annotations

import pytest

from app.models.response import (
    Confidence,
    DateDeclarationCandidate,
    DateDeclarationsFieldResult,
    ErrorCode,
    Fields,
    FieldStatus,
    ImageResult,
    ImageStatus,
    ManufacturerCandidate,
    ManufacturerFieldResult,
    MRPCandidate,
    MRPFieldResult,
    NetQuantityCandidate,
    NetQuantityFieldResult,
    ScanError,
    ScanResponse,
    ScanStatus,
    ScanSummary,
)


def make_scan_response(
    *,
    scan_id: str = "scan-001",
    status: ScanStatus = ScanStatus.SUCCESS,
    images: list[ImageResult] | None = None,
    mrp_status: FieldStatus = FieldStatus.NOT_FOUND,
    mrp_candidates: list[MRPCandidate] | None = None,
    quantity_status: FieldStatus = FieldStatus.NOT_FOUND,
    quantity_candidates: list[NetQuantityCandidate] | None = None,
    date_status: FieldStatus = FieldStatus.NOT_FOUND,
    date_candidates: list[DateDeclarationCandidate] | None = None,
    manufacturer_status: FieldStatus = FieldStatus.NOT_FOUND,
    manufacturer_candidates: list[ManufacturerCandidate] | None = None,
    errors: list[ScanError] | None = None,
    images_received: int = 1,
    images_processed: int = 1,
    images_failed: int = 0,
) -> ScanResponse:
    if images is None:
        images = [ImageResult(image_id="front", status=ImageStatus.SUCCESS, text_detected=True, raw_text="...")]

    fields = Fields(
        mrp=MRPFieldResult(status=mrp_status, candidates=mrp_candidates or []),
        net_quantity=NetQuantityFieldResult(status=quantity_status, candidates=quantity_candidates or []),
        date_declarations=DateDeclarationsFieldResult(status=date_status, candidates=date_candidates or []),
        manufacturer_declarations=ManufacturerFieldResult(
            status=manufacturer_status, candidates=manufacturer_candidates or []
        ),
    )

    return ScanResponse(
        scan_id=scan_id,
        status=status,
        summary=ScanSummary(
            images_received=images_received,
            images_processed=images_processed,
            images_failed=images_failed,
        ),
        images=images,
        fields=fields,
        errors=errors or [],
    )


def mrp_candidate(value: float = 50.0, raw: str = "MRP Rs. 50", image_id: str = "front", confidence=Confidence.HIGH):
    return MRPCandidate(
        raw_text=raw,
        normalized_value=value,
        currency="INR",
        confidence=confidence,
        source_image_id=image_id,
        bounding_box=None,
    )


def quantity_candidate(value: float = 200.0, unit: str = "g", raw: str = "200 g", image_id: str = "front"):
    return NetQuantityCandidate(
        raw_text=raw,
        value=value,
        unit=unit,
        confidence=Confidence.HIGH,
        source_image_id=image_id,
        bounding_box=None,
    )


def date_candidate(
    declaration_type: str = "manufacturing",
    normalized_value: str | None = "2026-01-01",
    raw: str = "MFG: JAN 2026",
    label: str = "Manufacturing Date",
    image_id: str = "front",
):
    return DateDeclarationCandidate(
        label=label,
        raw_value=raw,
        normalized_value=normalized_value,
        declaration_type=declaration_type,
        confidence=Confidence.HIGH,
        source_image_id=image_id,
        bounding_box=None,
    )


def manufacturer_candidate(raw: str = "Acme Foods Pvt Ltd", label: str = "Manufacturer", image_id: str = "front"):
    return ManufacturerCandidate(
        label=label,
        raw_text=raw,
        confidence=Confidence.HIGH,
        source_image_id=image_id,
        bounding_box=None,
    )


@pytest.fixture
def scan_factory():
    return make_scan_response
