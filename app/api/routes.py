"""API routes for the OCR service."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.dependencies import get_orchestrator
from app.models.request import ScanRequest
from app.models.response import ScanResponse
from app.services.orchestrator import OCROrchestrator
from app.services.report_service import (
    dummy_scan_result,
    generate_docx_report,
    generate_pdf_report,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_scan_result(scan_id: str) -> dict[str, Any] | None:
    """Temporary database adapter; replace with the project's persisted scan lookup.

    The single demo ID enables local endpoint testing while unknown IDs correctly
    produce a 404 response.
    """
    return dummy_scan_result(scan_id) if scan_id == "demo-scan-001" else None


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/ocr/scan", response_model=ScanResponse)
def scan(
    request: ScanRequest,
    orchestrator: OCROrchestrator = Depends(get_orchestrator),
) -> ScanResponse:
    logger.info("scan_id=%s stage=received images=%d", request.scan_id, len(request.images))
    return orchestrator.run_scan(request)


@router.post("/reports/{scan_id}/pdf")
def download_pdf_report(scan_id: str) -> Response:
    """Build and download a PDF compliance report for an existing scan."""
    result = get_scan_result(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scan result '{scan_id}' was not found.")
    return Response(
        content=generate_pdf_report(result),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="compliance_report_{scan_id}.pdf"'
        },
    )


@router.post("/reports/{scan_id}/editable")
def download_editable_report(scan_id: str) -> Response:
    """Build and download an editable DOCX compliance report for an existing scan."""
    result = get_scan_result(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scan result '{scan_id}' was not found.")
    return Response(
        content=generate_docx_report(result),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="compliance_report_{scan_id}.docx"'
        },
    )
