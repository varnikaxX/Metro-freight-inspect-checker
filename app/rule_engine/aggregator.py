"""Compliance aggregator: reduces a list of Findings into one
OverallStatus.

Deterministic precedence (highest wins), documented here as the single
source of truth for this behavior:

    1. VIOLATION        -- if ANY finding is a violation, the scan is
                            not compliant, full stop. A passing field
                            never masks a failing one.
    2. REVIEW_REQUIRED   -- if there is no violation but at least one
                            finding needs human review (ambiguous
                            evidence, unparsable value, etc.), the scan
                            cannot be called compliant either.
    3. NOT_EVALUATED     -- if there is no violation and nothing needs
                            review, but at least one rule could not be
                            evaluated (insufficient evidence), the scan
                            is incomplete rather than confirmed
                            compliant.
    4. COMPLIANT         -- only if every finding is COMPLIANT (and
                            there is at least one finding at all).

An empty finding list (e.g. an empty ruleset) yields NOT_EVALUATED --
"no rules ran" is never reported as COMPLIANT, since that would be an
unsubstantiated claim per the explainability requirement (every overall
status must be traceable back to individual findings).
"""
from __future__ import annotations

from app.rule_engine.models import Finding, FindingStatus, OverallStatus

_PRECEDENCE: list[tuple[FindingStatus, OverallStatus]] = [
    (FindingStatus.VIOLATION, OverallStatus.VIOLATION),
    (FindingStatus.REVIEW_REQUIRED, OverallStatus.REVIEW_REQUIRED),
    (FindingStatus.NOT_EVALUATED, OverallStatus.NOT_EVALUATED),
]


def aggregate(findings: list[Finding]) -> OverallStatus:
    if not findings:
        return OverallStatus.NOT_EVALUATED

    statuses = {f.status for f in findings}

    for finding_status, overall_status in _PRECEDENCE:
        if finding_status in statuses:
            return overall_status

    # Every finding was COMPLIANT.
    return OverallStatus.COMPLIANT
