from __future__ import annotations

from app.rule_engine.aggregator import aggregate
from app.rule_engine.models import Finding, FindingStatus, OverallStatus, Severity


def _finding(status: FindingStatus, rule_id: str = "R-1", field: str = "mrp") -> Finding:
    return Finding(
        rule_id=rule_id,
        field=field,
        status=status,
        severity=Severity.HIGH,
        message="msg",
        evidence=[],
        rule_version="1.0.0",
    )


def test_overall_compliance_when_all_compliant():
    """#16: Overall compliance aggregation."""
    findings = [_finding(FindingStatus.COMPLIANT), _finding(FindingStatus.COMPLIANT, rule_id="R-2")]
    assert aggregate(findings) == OverallStatus.COMPLIANT


def test_single_violation_overrides_compliant_findings():
    findings = [
        _finding(FindingStatus.COMPLIANT, rule_id="R-1"),
        _finding(FindingStatus.VIOLATION, rule_id="R-2"),
        _finding(FindingStatus.COMPLIANT, rule_id="R-3"),
    ]
    assert aggregate(findings) == OverallStatus.VIOLATION


def test_review_required_beats_compliant_but_not_violation():
    findings = [_finding(FindingStatus.COMPLIANT), _finding(FindingStatus.REVIEW_REQUIRED, rule_id="R-2")]
    assert aggregate(findings) == OverallStatus.REVIEW_REQUIRED

    findings_with_violation = findings + [_finding(FindingStatus.VIOLATION, rule_id="R-3")]
    assert aggregate(findings_with_violation) == OverallStatus.VIOLATION


def test_not_evaluated_beats_compliant_but_not_review_or_violation():
    findings = [_finding(FindingStatus.COMPLIANT), _finding(FindingStatus.NOT_EVALUATED, rule_id="R-2")]
    assert aggregate(findings) == OverallStatus.NOT_EVALUATED

    with_review = findings + [_finding(FindingStatus.REVIEW_REQUIRED, rule_id="R-3")]
    assert aggregate(with_review) == OverallStatus.REVIEW_REQUIRED


def test_empty_findings_list_is_not_evaluated_not_compliant():
    assert aggregate([]) == OverallStatus.NOT_EVALUATED
