"""Base validator.

Implements the template-method pattern so that the §8 requirement
("multiple candidates / conflict must never be silently resolved by
picking a candidate; the normal outcome is REVIEW_REQUIRED unless a
deterministic rule can resolve the ambiguity") is enforced in ONE place
rather than repeated in every concrete validator.

Concrete validators only need to implement ``_validate_impl`` for the
"normal" (single, agreed-upon evidence) case. They may optionally
override ``try_resolve_ambiguity`` if a specific rule type ever gains a
genuine deterministic way to resolve multiple candidates -- none do
today, so the default always defers to REVIEW_REQUIRED.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.rule_engine.models import FieldAssessment, FieldStatus, Finding, FindingStatus, Rule


class Validator(ABC):
    def validate(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding:
        if assessment.ocr_status in (FieldStatus.MULTIPLE_CANDIDATES, FieldStatus.CONFLICT):
            resolved = self.try_resolve_ambiguity(rule, assessment, all_assessments, ruleset_version)
            if resolved is not None:
                return resolved
            return self._finding(
                rule,
                status=FindingStatus.REVIEW_REQUIRED,
                message=(
                    f"{rule.message} Cannot be automatically confirmed: OCR detected "
                    f"{assessment.ocr_status.value.replace('_', ' ')} for this field."
                ),
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
                reason="ambiguous_evidence",
            )

        return self._validate_impl(rule, assessment, all_assessments, ruleset_version)

    def try_resolve_ambiguity(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding | None:
        """Override to deterministically resolve MULTIPLE_CANDIDATES /
        CONFLICT for a specific rule type. Default: no resolution, i.e.
        always fall back to REVIEW_REQUIRED (the safe default)."""
        return None

    @abstractmethod
    def _validate_impl(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding:
        """Handle the FOUND / NOT_FOUND cases. MULTIPLE_CANDIDATES and
        CONFLICT are already handled by validate() and never reach here."""
        raise NotImplementedError

    @staticmethod
    def _finding(
        rule: Rule,
        *,
        status: FindingStatus,
        message: str,
        evidence,
        ruleset_version: str,
        reason: str | None = None,
    ) -> Finding:
        return Finding(
            rule_id=rule.rule_id,
            field=rule.field,
            status=status,
            severity=rule.severity,
            message=message,
            evidence=list(evidence),
            rule_version=ruleset_version,
            reason=reason,
        )
