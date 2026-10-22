"""FORMAT validator: does a candidate satisfy a defined format?

Rule params supported:
    "source": one of "unit" | "raw_text" | "normalized_value"
              (default: "unit") -- which Evidence attribute to check.
    "allowed_values": list[str] -- exact-match allow-list (case-insensitive).
    "pattern": str -- regex the source value must fully match.

Exactly one of "allowed_values" / "pattern" is expected; if both are
given, "allowed_values" takes precedence to keep behavior deterministic.
"""
from __future__ import annotations

import re

from app.rule_engine.models import FieldAssessment, FieldStatus, Finding, FindingStatus, Rule
from app.rule_engine.validators.base import Validator


class FormatValidator(Validator):
    def _validate_impl(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding:
        if assessment.ocr_status == FieldStatus.NOT_FOUND:
            return self._finding(
                rule,
                status=FindingStatus.NOT_EVALUATED,
                message=f"{rule.message} No value was detected to check.",
                evidence=[],
                ruleset_version=ruleset_version,
                reason="no_value_present",
            )

        candidate = assessment.candidates[0] if assessment.candidates else None
        if candidate is None:
            return self._finding(  # pragma: no cover - FOUND implies >=1 candidate
                rule,
                status=FindingStatus.REVIEW_REQUIRED,
                message=f"{rule.message} No evidence available despite FOUND status.",
                evidence=[],
                ruleset_version=ruleset_version,
                reason="missing_evidence_despite_found",
            )

        source = rule.params.get("source", "unit")
        raw_value = getattr(candidate, source, None)

        if raw_value is None:
            return self._finding(
                rule,
                status=FindingStatus.REVIEW_REQUIRED,
                message=f"{rule.message} No '{source}' value present to check format against.",
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
                reason="missing_format_source",
            )

        ok = self._matches(str(raw_value), rule.params)
        status = FindingStatus.COMPLIANT if ok else FindingStatus.VIOLATION
        message = (
            f"{rule.field.replace('_', ' ').title()} format passes validation."
            if ok
            else rule.message
        )
        return self._finding(
            rule,
            status=status,
            message=message,
            evidence=assessment.candidates,
            ruleset_version=ruleset_version,
        )

    @staticmethod
    def _matches(value: str, params: dict) -> bool:
        allowed_values = params.get("allowed_values")
        if allowed_values is not None:
            return value.strip().lower() in {str(v).strip().lower() for v in allowed_values}

        pattern = params.get("pattern")
        if pattern is not None:
            return re.fullmatch(pattern, value.strip()) is not None

        # No format constraint configured -- nothing to fail against.
        return True  # pragma: no cover - guarded by schema requiring one of the two
