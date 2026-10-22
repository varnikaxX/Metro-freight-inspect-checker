"""
routers/scan.py
----------------
Endpoints:
    POST /api/v1/scan               - upload a label image, run OCR + compliance checks
    GET  /api/v1/scans               - list scan history with violation counts
    GET  /api/v1/scans/{scan_id}     - full detail for a single scan
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from schemas import (
    ErrorResponse,
    FieldDetail,
    ScanListResponse,
    ScanResponse,
    ScanSummary,
    ViolationDetail,
)
from services import compliance, ocr
from services import supabase_client as db

logger = logging.getLogger("scan_router")

router = APIRouter(prefix="/api/v1", tags=["scans"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_scan(
    file: UploadFile = File(..., description="Package label image (jpg/png/webp)"),
    user_id: Optional[str] = Query(
        default=None, description="Optional authenticated user id"
    ),
) -> ScanResponse:
    """
    Full pipeline for a single label scan:
      1. Validate + read uploaded file
      2. Upload raw image bytes to Supabase Storage ('raw-labels' bucket)
      3. Insert an initial `scans` row with status=PROCESSING
      4. Run Google Cloud Vision OCR (document_text_detection)
      5. Run the LMR 2011 compliance rule engine on the extracted text
      6. Persist extracted_fields + violations
      7. Update scan status to COMPLETED (or FAILED on OCR failure)
      8. Return the full structured result
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum allowed size is 10 MB.",
        )

    # --- Step 1: upload raw image to Supabase Storage -----------------------
    try:
        raw_image_url = db.upload_image_to_storage(
            file_bytes=image_bytes,
            filename=file.filename or "label.jpg",
            content_type=file.content_type,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Storage upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to storage: {exc}",
        ) from exc

    # --- Step 2: create initial scan record ---------------------------------
    try:
        scan_row = db.insert_scan(
            raw_image_url=raw_image_url, user_id=user_id, status="PROCESSING"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to insert initial scan record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log scan: {exc}",
        ) from exc

    scan_id = scan_row["id"]

    # --- Step 3: run OCR ------------------------------------------------------
    ocr_result = ocr.extract_text_from_image(image_bytes)

    if not ocr_result["success"]:
        db.update_scan_status(scan_id, status="FAILED")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OCR processing failed: {ocr_result['error']}",
        )

    full_text = ocr_result["full_text"]
    if getattr(ocr.settings, "DEBUG_OCR", False):
        logger.info("Merged OCR text for scan %s: %r", scan_id, full_text)

    # --- Step 4: run compliance rule engine -----------------------------------
    # Pass structured OCR internally so extraction can use line proximity and boxes;
    # the persisted/API response remains the existing fields and full_text shape.
    fields, violations = compliance.run_compliance_check(ocr_result)
    if getattr(ocr.settings, "DEBUG_OCR", False):
        logger.info("Extracted fields for scan %s: %s", scan_id, fields)
        logger.info("Detected violations for scan %s: %s", scan_id, violations)

    try:
        saved_fields = db.insert_extracted_fields(scan_id, fields)
        saved_violations = db.insert_violations(scan_id, violations)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to persist fields/violations")
        db.update_scan_status(scan_id, status="FAILED")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist compliance results: {exc}",
        ) from exc

    # --- Step 5: finalize scan status ------------------------------------------
    updated_scan = db.update_scan_status(scan_id, status="COMPLETED")

    return ScanResponse(
        id=updated_scan["id"],
        user_id=updated_scan.get("user_id"),
        raw_image_url=updated_scan["raw_image_url"],
        pdf_report_url=updated_scan.get("pdf_report_url"),
        status=updated_scan["status"],
        created_at=updated_scan["created_at"],
        updated_at=updated_scan.get("updated_at"),
        extracted_fields=[FieldDetail(**{**saved, **{key: field.get(key) for key in ("verification_state", "candidate_status", "raw_text", "source_line", "confidence")}}) for saved, field in zip(saved_fields, fields)],
        violations=[ViolationDetail(**v) for v in saved_violations],
        full_text=full_text,
    )


@router.get(
    "/scans",
    response_model=ScanListResponse,
    responses={500: {"model": ErrorResponse}},
)
async def list_scans(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ScanListResponse:
    """Retrieve scan history with per-scan violation counts, most recent first."""
    try:
        scans = db.get_scan_history(limit=limit, offset=offset)
        total = db.count_scans()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch scan history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan history: {exc}",
        ) from exc

    return ScanListResponse(
        total=total,
        scans=[
            ScanSummary(
                id=s["id"],
                raw_image_url=s["raw_image_url"],
                pdf_report_url=s.get("pdf_report_url"),
                status=s["status"],
                created_at=s["created_at"],
                violation_count=s.get("violation_count", 0),
                is_compliant=s.get("is_compliant", True),
            )
            for s in scans
        ],
    )


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_scan(scan_id: UUID) -> ScanResponse:
    """Fetch full detail (fields + violations) for a single scan."""
    try:
        scan_row = db.get_scan_by_id(str(scan_id))
        if not scan_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan '{scan_id}' not found.",
            )

        fields = db.get_fields_for_scan(str(scan_id))
        violations = db.get_violations_for_scan(str(scan_id))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch scan detail")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan detail: {exc}",
        ) from exc

    return ScanResponse(
        id=scan_row["id"],
        user_id=scan_row.get("user_id"),
        raw_image_url=scan_row["raw_image_url"],
        pdf_report_url=scan_row.get("pdf_report_url"),
        status=scan_row["status"],
        created_at=scan_row["created_at"],
        updated_at=scan_row.get("updated_at"),
        extracted_fields=[FieldDetail(**f) for f in fields],
        violations=[ViolationDetail(**v) for v in violations],
        full_text=None,
    )
