"""
schemas.py
----------
Pydantic models used for request validation and response serialization
across the Legal Metrology Compliance Verification API.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Enums (kept as plain literals via str for simplicity / JSON friendliness)
# ============================================================================
class ScanStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# Field-level details (extracted_fields table)
# ============================================================================
class FieldDetail(BaseModel):
    id: Optional[UUID] = None
    scan_id: Optional[UUID] = None
    field_name: str = Field(..., description="Canonical LMR field name, e.g. 'MRP'")
    field_value: Optional[str] = Field(
        None, description="Raw value extracted from the label via OCR"
    )
    is_present: bool = Field(
        False, description="Whether this mandatory field was detected on the label"
    )
    created_at: Optional[datetime] = None
    verification_state: Optional[str] = None
    raw_text: Optional[str] = None
    source_line: Optional[str] = None
    confidence: Optional[float] = None
    candidate_status: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Violation-level details (violations table)
# ============================================================================
class ViolationDetail(BaseModel):
    id: Optional[UUID] = None
    scan_id: Optional[UUID] = None
    rule_code: str = Field(..., description="LMR 2011 rule identifier, e.g. 'LMR_R6_MRP_MISSING'")
    description: str = Field(..., description="Human-readable explanation of the violation")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Full scan detail response (GET /api/v1/scans/{scan_id})
# ============================================================================
class ScanResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    raw_image_url: str
    pdf_report_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    extracted_fields: List[FieldDetail] = Field(default_factory=list)
    violations: List[ViolationDetail] = Field(default_factory=list)
    full_text: Optional[str] = Field(
        None, description="Raw OCR full-text output, included on initial scan response"
    )

    class Config:
        from_attributes = True


# ============================================================================
# Lightweight scan summary for history/list views (GET /api/v1/scans)
# ============================================================================
class ScanSummary(BaseModel):
    id: UUID
    raw_image_url: str
    pdf_report_url: Optional[str] = None
    status: str
    created_at: datetime
    violation_count: int = 0
    is_compliant: bool = True

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    total: int
    scans: List[ScanSummary]


class ErrorResponse(BaseModel):
    detail: str
