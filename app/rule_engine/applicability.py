"""Applicability layer.

Answers: "should this rule even be evaluated?" This is kept strictly
separate from "did the rule pass?" (that question belongs to the
validators in ``validators/``).

Two situations currently make a rule inapplicable / not evaluable:

1. INSUFFICIENT_EVIDENCE -- the field's ``NOT_FOUND`` status cannot be
   trusted because OCR never got a usable look at any image in the
   scan (see adapter.py's ``evidence_reliable`` for exactly when this
   happens). Running a PRESENCE rule against this would produce a
   false VIOLATION, which project instructions explicitly forbid.

2. NOT_APPLICABLE -- reserved for future conditional rules (e.g. "only
   evaluate this rule if some other field has a certain value"). The
   current ruleset does not define any such rules, so this path is a
   documented extension point rather than active logic today. A rule
   may opt into this via an optional ``applies_if`` block in its
   ruleset entry (currently unused, validated as optional by the
   schema, and simply ignored if absent).
"""
from __future__ import annotations

from app.rule_engine.models import ApplicabilityStatus, FieldAssessment, FieldStatus, Rule


def determine_applicability(rule: Rule, assessment: FieldAssessment) -> ApplicabilityStatus:
    # Reserved extension point: a rule may declare `applies_if` in its
    # `params`, e.g. {"applies_if": {"field": "...", "status": "found"}}.
    # No current rule in ruleset.json uses this; left as a documented
    # no-op hook so adding conditional rules later doesn't require
    # touching engine.py.
    applies_if = rule.params.get("applies_if")
    if applies_if is not None:  # pragma: no cover - no rule exercises this today
        # Intentionally not implemented further: without a concrete
        # conditional rule in the spec, guessing at semantics here
        # would risk inventing requirements. Documented as a known
        # limitation rather than silently no-op'd without explanation.
        pass

    if assessment.ocr_status == FieldStatus.NOT_FOUND and not assessment.evidence_reliable:
        return ApplicabilityStatus.INSUFFICIENT_EVIDENCE

    return ApplicabilityStatus.APPLICABLE
