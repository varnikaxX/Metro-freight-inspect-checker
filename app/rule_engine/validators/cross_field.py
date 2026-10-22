"""CROSS_FIELD validator: relates two pieces of evidence to each other.

Currently supports one comparison, expressed via rule params:

    {
      "comparison": "date_after",
      "type_a": "manufacturing",
      "type_b": "expiry"
    }

which checks that the DateDeclarationCandidate whose ``declaration_type``
equals ``type_b`` is chronologically after the one whose
``declaration_type`` equals ``type_a``, using ``normalized_value``
(assumed ISO-8601 "YYYY-MM-DD", consistent with a normalized date
string). This assumption is documented in ruleset.json's rule comment
and here; if the actual DateExtractor normalizes dates differently,
only this function needs to change.

The validator receives ``all_assessments`` (not just the rule's own
field) so a future rule could genuinely compare across two *different*
OCR field groups (e.g. mrp vs net_quantity) without a design change --
today's only cross-field rule happens to compare two candidates within
the same field (date_declarations), which is why ``type_a``/``type_b``
are looked up inside ``assessment.candidates`` rather than in
``all_assessments``.
"""
from __future__ import annotations

from datetime import date, datetime

from app.rule_engine.models import Evidence, FieldAssessment, FieldStatus, Finding, FindingStatus, Rule
from app.rule_engine.validators.base import Validator

_SUPPORTED_COMPARISONS = {"date_after"}


def _find_by_declaration_type(candidates: list[Evidence], declaration_type: str) -> Evidence | None:
    for candidate in candidates:
        if candidate.declaration_type == declaration_type:
            return candidate
    return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


class CrossFieldValidator(Validator):
    def _validate_impl(
        self,
        rule: Rule,
        assessment: FieldAssessment,
        all_assessments: dict[str, FieldAssessment],
        ruleset_version: str,
    ) -> Finding:
        comparison = rule.params.get("comparison")
        if comparison not in _SUPPORTED_COMPARISONS:
            # Unrecognized comparison: fail safe rather than guess.
            return self._finding(  # pragma: no cover - guarded by schema
                rule,
                status=FindingStatus.NOT_EVALUATED,
                message=f"{rule.message} Unsupported comparison '{comparison}'.",
                evidence=[],
                ruleset_version=ruleset_version,
                reason="unsupported_comparison",
            )

        if assessment.ocr_status == FieldStatus.NOT_FOUND:
            return self._finding(
                rule,
                status=FindingStatus.NOT_EVALUATED,
                message=f"{rule.message} No date declarations were detected to compare.",
                evidence=[],
                ruleset_version=ruleset_version,
                reason="no_value_present",
            )

        type_a = rule.params.get("type_a")
        type_b = rule.params.get("type_b")
        candidate_a = _find_by_declaration_type(assessment.candidates, type_a)
        candidate_b = _find_by_declaration_type(assessment.candidates, type_b)

        if candidate_a is None or candidate_b is None:
            missing = [n for n, c in ((type_a, candidate_a), (type_b, candidate_b)) if c is None]
            return self._finding(
                rule,
                status=FindingStatus.NOT_EVALUATED,
                message=(
                    f"{rule.message} Comparison requires both '{type_a}' and '{type_b}' "
                    f"declarations; missing: {', '.join(missing)}."
                ),
                evidence=assessment.candidates,
                ruleset_version=ruleset_version,
                reason="insufficient_data_for_comparison",
            )

        date_a = _parse_date(candidate_a.normalized_value)
        date_b = _parse_date(candidate_b.normalized_value)

        if date_a is None or date_b is None:
            return self._finding(
                rule,
                status=FindingStatus.REVIEW_REQUIRED,
                message=f"{rule.message} One or both dates could not be parsed for comparison.",
                evidence=[candidate_a, candidate_b],
                ruleset_version=ruleset_version,
                reason="unparsable_date",
            )

        if date_b > date_a:
            return self._finding(
                rule,
                status=FindingStatus.COMPLIANT,
                message=f"{type_b.title()} date is after {type_a} date, as required.",
                evidence=[candidate_a, candidate_b],
                ruleset_version=ruleset_version,
            )

        return self._finding(
            rule,
            status=FindingStatus.VIOLATION,
            message=rule.message,
            evidence=[candidate_a, candidate_b],
            ruleset_version=ruleset_version,
        )
