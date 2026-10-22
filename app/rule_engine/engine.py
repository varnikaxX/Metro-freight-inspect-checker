"""Rule Engine entry point.

    ScanResponse
        -> adapter.to_field_assessments()
        -> applicability.determine_applicability() per rule
        -> validators.dispatch() per applicable rule
        -> Finding per rule
        -> aggregator.aggregate()
        -> ComplianceResponse

Deterministic: the same ScanResponse + the same ruleset version always
produces the same ComplianceResponse. No randomness, no wall-clock
dependence in the evaluation itself.
"""
from __future__ import annotations

from pathlib import Path

from app.models.response import ScanResponse
from app.rule_engine import aggregator
from app.rule_engine.adapter import to_field_assessments
from app.rule_engine.applicability import determine_applicability
from app.rule_engine.models import ApplicabilityStatus, ComplianceResponse, Finding, FindingStatus
from app.rule_engine.registry import RuleRegistry
from app.rule_engine.validators import dispatch


class RuleEngine:
    """Deterministic compliance evaluator.

    Usage:
        engine = RuleEngine()  # loads the default ruleset
        compliance_response = engine.evaluate(scan_response)
    """

    def __init__(self, registry: RuleRegistry | None = None, ruleset_path: Path | str | None = None) -> None:
        if registry is not None and ruleset_path is not None:
            raise ValueError("Pass either 'registry' or 'ruleset_path', not both.")
        if registry is not None:
            self._registry = registry
        elif ruleset_path is not None:
            self._registry = RuleRegistry(ruleset_path)
        else:
            self._registry = RuleRegistry()

    def evaluate(self, scan: ScanResponse) -> ComplianceResponse:
        assessments = to_field_assessments(scan)
        findings: list[Finding] = []

        for rule in self._registry.rules:
            assessment = assessments.get(rule.field)
            if assessment is None:  # pragma: no cover - guarded by registry field enum validation
                continue

            applicability = determine_applicability(rule, assessment)

            if applicability == ApplicabilityStatus.INSUFFICIENT_EVIDENCE:
                findings.append(
                    Finding(
                        rule_id=rule.rule_id,
                        field=rule.field,
                        status=FindingStatus.NOT_EVALUATED,
                        severity=rule.severity,
                        message=(
                            f"{rule.message} Could not be evaluated: OCR was unable to process "
                            f"any image in this scan, so a missing declaration cannot be confirmed."
                        ),
                        evidence=[],
                        rule_version=self._registry.version,
                        reason="insufficient_evidence",
                    )
                )
                continue

            if applicability == ApplicabilityStatus.NOT_APPLICABLE:
                # Rule genuinely does not apply in this context -- no
                # finding is produced (nothing to explain to a judge:
                # the rule simply wasn't relevant here).
                continue  # pragma: no cover - no rule in the current ruleset triggers this

            validator = dispatch(rule.type)
            finding = validator.validate(rule, assessment, assessments, self._registry.version)
            findings.append(finding)

        return ComplianceResponse(
            scan_id=scan.scan_id,
            overall_status=aggregator.aggregate(findings),
            findings=findings,
            ruleset_id=self._registry.ruleset_id,
            ruleset_version=self._registry.version,
        )
