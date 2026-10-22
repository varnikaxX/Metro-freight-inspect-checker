"""PRESENCE validator: is the required declaration available at all?

By the time this runs, applicability.py has already filtered out the
case where NOT_FOUND can't be trusted (INSUFFICIENT_EVIDENCE), and
base.Validator has already filtered out MULTIPLE_CANDIDATES/CONFLICT
(-> REVIEW_REQUIRED). So this only ever sees FOUND or a *trustworthy*
NOT_FOUND.
"""
from __future__ import annotations

from app.rule_engine.models import FieldAssessment, FieldStatus, Finding, FindingStatus, Rule
from app.rule_engine.validators.base import Validator


class PresenceValidator(Validator):
    def _validate_impl(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding:
        if assessment.ocr_status == FieldStatus.FOUND:
            return self._finding(
                rule,
                status=FindingStatus.COMPLIANT,
                message=f"{rule.field.replace('_', ' ').title()} declaration is present.",
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
            )

        if assessment.ocr_status == FieldStatus.NOT_FOUND:
            return self._finding(
                rule,
                status=FindingStatus.VIOLATION,
                message=rule.message,
                evidence=[],
                ruleset_version=ruleset_version,
            )

        # Defensive fallback: should be unreachable given base.Validator's
        # ambiguity handling and applicability.py's filtering, but never
        # silently guess at a presence result for an unexpected status.
        return self._finding(  # pragma: no cover
            rule,
            status=FindingStatus.REVIEW_REQUIRED,
            message=f"{rule.message} Unexpected OCR status: {assessment.ocr_status.value}.",
            evidence=assessment.candidates,
            ruleset_version=ruleset_version,
            reason="unexpected_status",
        )
