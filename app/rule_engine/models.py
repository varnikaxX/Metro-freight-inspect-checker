"""Internal Rule Engine data models.

These models are the Rule Engine's OWN vocabulary. Nothing below this
module (registry, applicability, validators, engine, aggregator) should
need to import anything from ``app.models.response`` -- that OCR-specific
knowledge is confined to ``adapter.py``.

Deliberately generic: a ``FieldAssessment`` can represent an MRP field,
a net-quantity field, a date-declarations field, or a manufacturer field
using the exact same shape. This is what lets the validators be
field-agnostic and lets a future 5th OCR field slot in without changing
these models.

Design note on ``FieldStatus``: it is re-exported (not re-defined) from
``app.models.response``. This is a deliberate, narrow exception to "the
Rule Engine must not know about OCR internals" -- FieldStatus
(found / not_found / multiple_candidates / conflict) is genuinely shared
vocabulary describing detection outcome, not an OCR implementation
detail like MRPCandidate or OCRProvider. The per-field Candidate and
FieldResult classes are NOT reused here; those get adapted into the
generic ``Evidence`` / ``FieldAssessment`` shapes below.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.ocr_document import BoundingBox
from app.models.response import FieldStatus

__all__ = [
    "FieldStatus",
    "Severity",
    "RuleType",
    "FindingStatus",
    "OverallStatus",
    "ApplicabilityStatus",
    "Evidence",
    "FieldAssessment",
    "Rule",
    "Finding",
    "ComplianceResponse",
]


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleType(str, Enum):
    PRESENCE = "PRESENCE"
    VALUE = "VALUE"
    FORMAT = "FORMAT"
    CROSS_FIELD = "CROSS_FIELD"


class FindingStatus(str, Enum):
    """Result of evaluating a single rule against a single field."""

    COMPLIANT = "COMPLIANT"
    VIOLATION = "VIOLATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_EVALUATED = "NOT_EVALUATED"


class OverallStatus(str, Enum):
    """Result of aggregating all findings for a scan. Same vocabulary as
    FindingStatus by design -- see aggregator.py for the precedence
    that reduces many findings to one overall status."""

    COMPLIANT = "COMPLIANT"
    VIOLATION = "VIOLATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_EVALUATED = "NOT_EVALUATED"


class ApplicabilityStatus(str, Enum):
    """Answers "should this rule even run?" -- kept separate from
    "did it pass?". See applicability.py."""

    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Evidence(BaseModel):
    """Generic evidence item. Shape-compatible with every OCR candidate
    type after adapter.py has converted it. Never fabricated -- every
    Evidence instance traces back to a real OCR candidate produced by
    the existing extractors."""

    raw_text: str | None = None
    normalized_value: Any | None = None
    label: str | None = None
    declaration_type: str | None = None
    unit: str | None = None
    currency: str | None = None
    confidence: str | None = None  # mirrors app.models.response.Confidence.value
    source_image_id: str
    bounding_box: BoundingBox | None = None

    model_config = {"frozen": True}


class FieldAssessment(BaseModel):
    """The Rule Engine's view of a single OCR field group, produced by
    adapting one ScanResponse.fields.<field_name>."""

    field_name: str
    ocr_status: FieldStatus
    candidates: list[Evidence] = Field(default_factory=list)

    # True unless this field's NOT_FOUND cannot be trusted because OCR
    # never had a chance to look (every image in the scan failed to
    # process). See adapter.py for exactly when this is set to False.
    evidence_reliable: bool = True


class Rule(BaseModel):
    """A single rule loaded from ruleset.json."""

    rule_id: str
    field: str
    type: RuleType
    severity: Severity
    message: str
    params: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """The explainable result of evaluating one rule against one field.

    Design note: ``evidence`` is always a list (empty when there is
    none), even for a single-item case. The prompt's illustrative
    examples showed an empty list for "no evidence" and a bare object
    for "one evidence item" -- this implementation standardizes on a
    list in both cases for a single consistent shape for API consumers
    (dashboard/frontend), rather than a field that changes type.
    """

    rule_id: str
    field: str
    status: FindingStatus
    severity: Severity
    message: str
    evidence: list[Evidence] = Field(default_factory=list)
    rule_version: str
    reason: str | None = None  # short machine-readable explanation, e.g. "ambiguous_evidence"


class ComplianceResponse(BaseModel):
    """Final output of RuleEngine.evaluate()."""

    scan_id: str
    overall_status: OverallStatus
    findings: list[Finding] = Field(default_factory=list)
    ruleset_id: str
    ruleset_version: str
