from app.models.response import FieldStatus
from app.rule_engine.models import FieldAssessment, FindingStatus, Rule, RuleType, Severity
from app.rule_engine.validators.presence import PresenceValidator


def test_presence_when_field_is_found():
    rule = Rule(
        rule_id="TEST-001",
        field="mrp",
        type=RuleType.PRESENCE,
        severity=Severity.HIGH,
        message="MRP is required.",
    )

    assessment = FieldAssessment(
        field_name="mrp",
        ocr_status=FieldStatus.FOUND,
        candidates=[],
    )

    result = PresenceValidator().validate(
        rule,
        assessment,
        {"mrp": assessment},
        "1.0.0",
    )

    assert result.status == FindingStatus.COMPLIANT


def test_presence_when_field_is_not_found():
    rule = Rule(
        rule_id="TEST-001",
        field="mrp",
        type=RuleType.PRESENCE,
        severity=Severity.HIGH,
        message="MRP is required.",
    )

    assessment = FieldAssessment(
        field_name="mrp",
        ocr_status=FieldStatus.NOT_FOUND,
        candidates=[],
    )

    result = PresenceValidator().validate(
        rule,
        assessment,
        {"mrp": assessment},
        "1.0.0",
    )

    assert result.status == FindingStatus.VIOLATION