"""Boundary between the existing OCR contract and the Rule Engine.

This is the ONLY module in the Rule Engine that is allowed to import
the per-field OCR models (MRPCandidate, NetQuantityCandidate, ...,
Fields, ScanResponse). Everything downstream (registry, applicability,
validators, engine, aggregator) works exclusively with the generic
``FieldAssessment`` / ``Evidence`` shapes from ``models.py``.

If the OCR team changes ScanResponse (e.g. adds a 5th field, renames a
candidate attribute, adds a new FieldStatus), this is the only file
that should need to change.

--------------------------------------------------------------------
KNOWN LIMITATION (documented per project instructions, not silently
worked around):

``FieldStatus.NOT_FOUND`` on its own does not distinguish between:
  (a) OCR successfully processed every image and genuinely found no
      declaration for this field, and
  (b) OCR could not process (some or all of) the images, so "not
      found" may just mean "never looked".

The current ScanResponse contract does not carry per-field visibility
into which image would have contained which field, so case (b) can
only be approximated at the whole-scan level via ``ScanResponse.status``
/ ``ScanResponse.summary``. Per an explicit product decision (2026-08),
this adapter approximates it conservatively but simply:

    - ScanStatus.FAILED   (images_processed == 0, i.e. EVERY image
      failed) -> NOT_FOUND is NOT trusted. Evidence is marked
      unreliable, and applicability.py will route this to
      NOT_EVALUATED instead of a false VIOLATION.
    - ScanStatus.PARTIAL  (some images failed, but at least one
      succeeded) -> NOT_FOUND IS still trusted at face value. We
      cannot know whether the missing field would have been on a
      failed image, so we accept this as a known false-negative risk
      rather than suppressing every presence check on any partial
      scan. This is a deliberate simplicity/precision trade-off, not
      an oversight -- if the OCR contract is later extended to say
      *which* image(s) a field extractor expected to search, this
      approximation should be replaced with a precise per-field check.
    - ScanStatus.SUCCESS -> NOT_FOUND is always trusted.
--------------------------------------------------------------------
"""
from __future__ import annotations

from app.models.response import (
    Confidence,
    DateDeclarationCandidate,
    Fields,
    ManufacturerCandidate,
    MRPCandidate,
    NetQuantityCandidate,
    ScanResponse,
    ScanStatus,
)
from app.rule_engine.models import Evidence, FieldAssessment

# The four field names this adapter (and the rest of the engine)
# currently knows about. This constant is the single place that would
# need to grow if the OCR contract adds a 5th field group.
KNOWN_FIELD_NAMES: tuple[str, ...] = (
    "mrp",
    "net_quantity",
    "date_declarations",
    "manufacturer_declarations",
)


def _confidence_value(confidence: Confidence) -> str:
    return confidence.value if isinstance(confidence, Confidence) else str(confidence)


def _mrp_evidence(candidate: MRPCandidate) -> Evidence:
    return Evidence(
        raw_text=candidate.raw_text,
        normalized_value=candidate.normalized_value,
        currency=candidate.currency,
        confidence=_confidence_value(candidate.confidence),
        source_image_id=candidate.source_image_id,
        bounding_box=candidate.bounding_box,
    )


def _quantity_evidence(candidate: NetQuantityCandidate) -> Evidence:
    return Evidence(
        raw_text=candidate.raw_text,
        normalized_value=candidate.value,
        unit=candidate.unit,
        confidence=_confidence_value(candidate.confidence),
        source_image_id=candidate.source_image_id,
        bounding_box=candidate.bounding_box,
    )


def _date_evidence(candidate: DateDeclarationCandidate) -> Evidence:
    return Evidence(
        raw_text=candidate.raw_value,
        normalized_value=candidate.normalized_value,
        label=candidate.label,
        declaration_type=candidate.declaration_type,
        confidence=_confidence_value(candidate.confidence),
        source_image_id=candidate.source_image_id,
        bounding_box=candidate.bounding_box,
    )


def _manufacturer_evidence(candidate: ManufacturerCandidate) -> Evidence:
    return Evidence(
        raw_text=candidate.raw_text,
        normalized_value=None,
        label=candidate.label,
        confidence=_confidence_value(candidate.confidence),
        source_image_id=candidate.source_image_id,
        bounding_box=candidate.bounding_box,
    )


def _is_evidence_reliable(scan: ScanResponse) -> bool:
    """False only when OCR never successfully processed a single image
    in this scan. See module docstring for the full rationale."""
    return scan.status != ScanStatus.FAILED


def _build_assessment(
    field_name: str,
    ocr_status,
    evidence_items: list[Evidence],
    evidence_reliable: bool,
) -> FieldAssessment:
    return FieldAssessment(
        field_name=field_name,
        ocr_status=ocr_status,
        candidates=evidence_items,
        evidence_reliable=evidence_reliable,
    )


def to_field_assessments(scan: ScanResponse) -> dict[str, FieldAssessment]:
    """Convert ScanResponse.fields into the Rule Engine's generic
    representation. This is the single entry point the rest of the
    Rule Engine (via engine.py) uses to consume OCR output."""
    fields: Fields = scan.fields
    reliable = _is_evidence_reliable(scan)

    return {
        "mrp": _build_assessment(
            "mrp",
            fields.mrp.status,
            [_mrp_evidence(c) for c in fields.mrp.candidates],
            reliable,
        ),
        "net_quantity": _build_assessment(
            "net_quantity",
            fields.net_quantity.status,
            [_quantity_evidence(c) for c in fields.net_quantity.candidates],
            reliable,
        ),
        "date_declarations": _build_assessment(
            "date_declarations",
            fields.date_declarations.status,
            [_date_evidence(c) for c in fields.date_declarations.candidates],
            reliable,
        ),
        "manufacturer_declarations": _build_assessment(
            "manufacturer_declarations",
            fields.manufacturer_declarations.status,
            [_manufacturer_evidence(c) for c in fields.manufacturer_declarations.candidates],
            reliable,
        ),
    }
