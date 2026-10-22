"""VALUE validator: is a normalized numeric candidate within an
acceptable range?

Rule params supported (all optional, at least one expected):
    "min": number   -- value must be > min (exclusive)
    "min_inclusive": number -- value must be >= min_inclusive
    "max": number   -- value must be < max (exclusive)
    "max_inclusive": number -- value must be <= max_inclusive

This validator deliberately does NOT judge presence -- if the field is
NOT_FOUND, there is nothing to validate and that is a different rule's
(PRESENCE) concern. Penalizing the same missing data twice, under two
different rule_ids, would misrepresent the scan to a judge/dashboard.
"""
from __future__ import annotations

from app.rule_engine.models import FieldAssessment, FieldStatus, Finding, FindingStatus, Rule
from app.rule_engine.validators.base import Validator


class ValueValidator(Validator):
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
                message=f"{rule.message} No value was detected to validate.",
                evidence=[],
                ruleset_version=ruleset_version,
                reason="no_value_present",
            )

        # ocr_status == FOUND here (ambiguity already handled upstream).
        candidate = assessment.candidates[0] if assessment.candidates else None
        value = candidate.normalized_value if candidate is not None else None

        if value is None:
            # OCR found *something* (raw text) but could not normalize
            # it into a comparable value. We cannot validate a value we
            # don't have -- this is evidence for a human, not a clean
            # pass or fail.
            return self._finding(
                rule,
                status=FindingStatus.REVIEW_REQUIRED,
                message=f"{rule.message} Detected text could not be normalized into a comparable value.",
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
                reason="unnormalized_value",
            )

        ok = self._within_bounds(value, rule.params)
        if ok:
            return self._finding(
                rule,
                status=FindingStatus.COMPLIANT,
                message=f"{rule.field.replace('_', ' ').title()} value passes validation.",
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
            )

        return self._finding(
            rule,
            status=FindingStatus.VIOLATION,
            message=rule.message,
            evidence=assessment.candidates,
            ruleset_version=ruleset_version,
        )

    @staticmethod
    def _within_bounds(value: float, params: dict) -> bool:
        if "min" in params and not (value > params["min"]):
            return False
        if "min_inclusive" in params and not (value >= params["min_inclusive"]):
            return False
        if "max" in params and not (value < params["max"]):
            return False
        if "max_inclusive" in params and not (value <= params["max_inclusive"]):
            return False
        return True
