from __future__ import annotations

from app.models.response import Confidence, FieldStatus, ScanStatus
from app.rule_engine.engine import RuleEngine
from app.rule_engine.models import FindingStatus, OverallStatus
from app.rule_engine.tests.rule_engine.conftest import (
    date_candidate,
    make_scan_response,
    manufacturer_candidate,
    mrp_candidate,
    quantity_candidate,
)


def _findings_for(compliance_response, rule_id):
    return [f for f in compliance_response.findings if f.rule_id == rule_id]


def test_mrp_found_and_valid_is_compliant():
    """#1: MRP found + valid -> expected compliant result."""
    scan = make_scan_response(
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=50.0)],
    )
    result = RuleEngine().evaluate(scan)

    presence = _findings_for(result, "MRP-001")[0]
    value = _findings_for(result, "MRP-002")[0]
    assert presence.status == FindingStatus.COMPLIANT
    assert value.status == FindingStatus.COMPLIANT
    assert presence.evidence[0].normalized_value == 50.0


def test_mrp_not_found_produces_violation():
    """#2: MRP not found -> expected rule result (VIOLATION), not silently ignored."""
    scan = make_scan_response(mrp_status=FieldStatus.NOT_FOUND)
    result = RuleEngine().evaluate(scan)

    presence = _findings_for(result, "MRP-001")[0]
    assert presence.status == FindingStatus.VIOLATION
    assert presence.evidence == []

    value = _findings_for(result, "MRP-002")[0]
    assert value.status == FindingStatus.NOT_EVALUATED  # nothing to validate


def test_net_quantity_found_and_valid():
    """#3: Net quantity found + valid."""
    scan = make_scan_response(
        quantity_status=FieldStatus.FOUND,
        quantity_candidates=[quantity_candidate(value=250, unit="g")],
    )
    result = RuleEngine().evaluate(scan)
    assert _findings_for(result, "QTY-001")[0].status == FindingStatus.COMPLIANT
    assert _findings_for(result, "QTY-002")[0].status == FindingStatus.COMPLIANT
    assert _findings_for(result, "QTY-003")[0].status == FindingStatus.COMPLIANT


def test_net_quantity_invalid_unit_is_violation():
    scan = make_scan_response(
        quantity_status=FieldStatus.FOUND,
        quantity_candidates=[quantity_candidate(value=250, unit="bananas")],
    )
    result = RuleEngine().evaluate(scan)
    assert _findings_for(result, "QTY-003")[0].status == FindingStatus.VIOLATION


def test_date_declaration_found_and_valid():
    """#4: Date declaration found + valid."""
    scan = make_scan_response(
        date_status=FieldStatus.FOUND,
        date_candidates=[
            date_candidate(declaration_type="manufacturing", normalized_value="2026-01-01"),
            date_candidate(declaration_type="expiry", normalized_value="2027-01-01", label="Expiry", raw="EXP 2027"),
        ],
    )
    result = RuleEngine().evaluate(scan)
    assert _findings_for(result, "DATE-001")[0].status == FindingStatus.COMPLIANT
    assert _findings_for(result, "DATE-002")[0].status == FindingStatus.COMPLIANT


def test_date_cross_field_violation_when_expiry_before_manufacturing():
    """#14: Cross-field validation."""
    scan = make_scan_response(
        date_status=FieldStatus.FOUND,
        date_candidates=[
            date_candidate(declaration_type="manufacturing", normalized_value="2026-06-01"),
            date_candidate(declaration_type="expiry", normalized_value="2026-01-01", label="Expiry", raw="EXP JAN 2026"),
        ],
    )
    result = RuleEngine().evaluate(scan)
    cross = _findings_for(result, "DATE-002")[0]
    assert cross.status == FindingStatus.VIOLATION


def test_date_cross_field_not_evaluated_when_only_one_type_present():
    scan = make_scan_response(
        date_status=FieldStatus.FOUND,
        date_candidates=[date_candidate(declaration_type="manufacturing", normalized_value="2026-06-01")],
    )
    result = RuleEngine().evaluate(scan)
    cross = _findings_for(result, "DATE-002")[0]
    assert cross.status == FindingStatus.NOT_EVALUATED


def test_manufacturer_declaration_found_and_valid():
    """#5: Manufacturer declaration found + valid."""
    scan = make_scan_response(
        manufacturer_status=FieldStatus.FOUND,
        manufacturer_candidates=[manufacturer_candidate(raw="Acme Foods Pvt Ltd")],
    )
    result = RuleEngine().evaluate(scan)
    assert _findings_for(result, "MFR-001")[0].status == FindingStatus.COMPLIANT


def test_multiple_candidates_yields_review_required():
    """#6: Multiple candidates -> REVIEW_REQUIRED."""
    scan = make_scan_response(
        mrp_status=FieldStatus.MULTIPLE_CANDIDATES,
        mrp_candidates=[mrp_candidate(value=50.0), mrp_candidate(value=55.0, image_id="back")],
    )
    result = RuleEngine().evaluate(scan)
    presence = _findings_for(result, "MRP-001")[0]
    assert presence.status == FindingStatus.REVIEW_REQUIRED
    assert presence.reason == "ambiguous_evidence"
    assert len(presence.evidence) == 2  # no candidate silently discarded


def test_conflict_yields_review_required():
    """#7: Conflict -> REVIEW_REQUIRED."""
    scan = make_scan_response(
        mrp_status=FieldStatus.CONFLICT,
        mrp_candidates=[mrp_candidate(value=50.0), mrp_candidate(value=999.0, image_id="back")],
    )
    result = RuleEngine().evaluate(scan)
    presence = _findings_for(result, "MRP-001")[0]
    assert presence.status == FindingStatus.REVIEW_REQUIRED
    value_finding = _findings_for(result, "MRP-002")[0]
    assert value_finding.status == FindingStatus.REVIEW_REQUIRED  # never guesses which candidate is right


def test_low_confidence_evidence_still_evaluated_but_confidence_is_visible():
    """#8: Low confidence handling -- the engine does not silently
    reject low-confidence evidence, but the confidence is preserved in
    the finding so a human/dashboard can weigh it."""
    scan = make_scan_response(
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=50.0, confidence=Confidence.LOW)],
    )
    result = RuleEngine().evaluate(scan)
    presence = _findings_for(result, "MRP-001")[0]
    assert presence.status == FindingStatus.COMPLIANT
    assert presence.evidence[0].confidence == "LOW"


def test_scan_status_partial_still_evaluates_rules_normally():
    """#9: OCR scan status = PARTIAL."""
    scan = make_scan_response(
        status=ScanStatus.PARTIAL,
        images_received=2,
        images_processed=1,
        images_failed=1,
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=50.0)],
    )
    result = RuleEngine().evaluate(scan)
    assert _findings_for(result, "MRP-001")[0].status == FindingStatus.COMPLIANT
    # A field genuinely not found on a partial scan is still trusted (per product decision).
    assert _findings_for(result, "QTY-001")[0].status == FindingStatus.VIOLATION


def test_scan_status_failed_never_produces_false_violation():
    """#10: OCR scan status = FAILED must not yield fabricated VIOLATIONs."""
    scan = make_scan_response(
        status=ScanStatus.FAILED,
        images_received=1,
        images_processed=0,
        images_failed=1,
    )
    result = RuleEngine().evaluate(scan)

    for finding in result.findings:
        assert finding.status != FindingStatus.VIOLATION

    presence = _findings_for(result, "MRP-001")[0]
    assert presence.status == FindingStatus.NOT_EVALUATED
    assert presence.reason == "insufficient_evidence"
    assert result.overall_status == OverallStatus.NOT_EVALUATED


def test_image_processing_failure_is_isolated_to_not_evaluated():
    """#11: Image processing failure -- verified via the FAILED-scan path
    (the only scan-level signal ScanResponse exposes to the Rule Engine)."""
    scan = make_scan_response(status=ScanStatus.FAILED, images_processed=0, images_failed=1)
    result = RuleEngine().evaluate(scan)
    assert all(f.status in (FindingStatus.NOT_EVALUATED,) for f in result.findings)


def test_missing_evidence_never_fabricated():
    """#12: Missing evidence -- a VIOLATION finding for a genuinely
    absent field must carry NO fabricated evidence."""
    scan = make_scan_response(mrp_status=FieldStatus.NOT_FOUND)
    result = RuleEngine().evaluate(scan)
    presence = _findings_for(result, "MRP-001")[0]
    assert presence.evidence == []


def test_invalid_normalized_value_triggers_review_required():
    """#13: Invalid normalized value (present in text but not
    normalizable) -> REVIEW_REQUIRED, not a silent pass or fail."""
    scan = make_scan_response(
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=None, raw="MRP: illegible")],
    )
    result = RuleEngine().evaluate(scan)
    value_finding = _findings_for(result, "MRP-002")[0]
    assert value_finding.status == FindingStatus.REVIEW_REQUIRED
    assert value_finding.reason == "unnormalized_value"


def test_multiple_rules_producing_multiple_findings():
    """#15: Multiple rules producing multiple findings for a fully
    populated, compliant scan."""
    scan = make_scan_response(
        mrp_status=FieldStatus.FOUND,
        mrp_candidates=[mrp_candidate(value=50.0)],
        quantity_status=FieldStatus.FOUND,
        quantity_candidates=[quantity_candidate(value=250, unit="g")],
        date_status=FieldStatus.FOUND,
        date_candidates=[
            date_candidate(declaration_type="manufacturing", normalized_value="2026-01-01"),
            date_candidate(declaration_type="expiry", normalized_value="2027-01-01", label="Expiry", raw="EXP 2027"),
        ],
        manufacturer_status=FieldStatus.FOUND,
        manufacturer_candidates=[manufacturer_candidate()],
    )
    result = RuleEngine().evaluate(scan)

    expected_rule_ids = {
        "MRP-001", "MRP-002", "QTY-001", "QTY-002", "QTY-003", "DATE-001", "DATE-002", "MFR-001",
    }
    assert {f.rule_id for f in result.findings} == expected_rule_ids
    assert result.overall_status == OverallStatus.COMPLIANT


def test_rule_version_appears_in_every_finding():
    """#19: Rule version appears in findings."""
    scan = make_scan_response(mrp_status=FieldStatus.NOT_FOUND)
    result = RuleEngine().evaluate(scan)
    assert result.ruleset_version == "1.0.0"
    for finding in result.findings:
        assert finding.rule_version == "1.0.0"


def test_compliance_response_traceable_to_findings():
    """Explainability: overall_status must be derivable from findings alone."""
    scan = make_scan_response(mrp_status=FieldStatus.NOT_FOUND)
    result = RuleEngine().evaluate(scan)
    from app.rule_engine.aggregator import aggregate

    assert result.overall_status == aggregate(result.findings)
