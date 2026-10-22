from __future__ import annotations

from app.models.response import FieldStatus, ScanStatus
from app.rule_engine.adapter import to_field_assessments
from app.rule_engine.tests.rule_engine.conftest import (
    date_candidate,
    make_scan_response,
    manufacturer_candidate,
    mrp_candidate,
    quantity_candidate,
)


def test_adapter_converts_all_four_field_types():
    """#20: Adapter correctly converts all four OCR field types."""
    scan = make_scan_response(
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=99.5, raw="MRP: Rs 99.50")],
        quantity_status=FieldStatus.FOUND,
        quantity_candidates=[quantity_candidate(value=500, unit="ml")],
        date_status=FieldStatus.FOUND,
        date_candidates=[date_candidate()],
        manufacturer_status=FieldStatus.FOUND,
        manufacturer_candidates=[manufacturer_candidate(raw="Acme Pvt Ltd")],
    )

    assessments = to_field_assessments(scan)

    assert set(assessments.keys()) == {"mrp", "net_quantity", "date_declarations", "manufacturer_declarations"}

    mrp = assessments["mrp"]
    assert mrp.ocr_status == FieldStatus.FOUND
    assert mrp.candidates[0].normalized_value == 99.5
    assert mrp.candidates[0].currency == "INR"
    assert mrp.candidates[0].raw_text == "MRP: Rs 99.50"

    qty = assessments["net_quantity"]
    assert qty.candidates[0].normalized_value == 500
    assert qty.candidates[0].unit == "ml"

    dates = assessments["date_declarations"]
    assert dates.candidates[0].declaration_type == "manufacturing"
    assert dates.candidates[0].normalized_value == "2026-01-01"

    mfr = assessments["manufacturer_declarations"]
    assert mfr.candidates[0].raw_text == "Acme Pvt Ltd"
    assert mfr.candidates[0].label == "Manufacturer"


def test_adapter_marks_evidence_unreliable_when_scan_failed():
    scan = make_scan_response(
        status=ScanStatus.FAILED,
        mrp_status=FieldStatus.NOT_FOUND,
        images_processed=0,
        images_failed=1,
    )
    assessments = to_field_assessments(scan)
    assert assessments["mrp"].evidence_reliable is False


def test_adapter_trusts_not_found_on_partial_scan():
    """Product decision: partial scans (some images failed, at least one
    succeeded) still trust NOT_FOUND at face value."""
    scan = make_scan_response(
        status=ScanStatus.PARTIAL,
        mrp_status=FieldStatus.NOT_FOUND,
        images_received=2,
        images_processed=1,
        images_failed=1,
    )
    assessments = to_field_assessments(scan)
    assert assessments["mrp"].evidence_reliable is True


def test_adapter_trusts_not_found_on_full_success():
    scan = make_scan_response(status=ScanStatus.SUCCESS, mrp_status=FieldStatus.NOT_FOUND)
    assessments = to_field_assessments(scan)
    assert assessments["mrp"].evidence_reliable is True
