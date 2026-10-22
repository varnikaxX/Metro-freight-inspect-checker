"""Multi-image aggregation.

Combines per-image extraction candidates into the final field-level
results. Conflicting values are always preserved -- this layer never
decides which candidate is "correct". Only obvious exact duplicates
are removed.
"""
from __future__ import annotations

from app.models.response import (
    DateDeclarationCandidate,
    DateDeclarationsFieldResult,
    Fields,
    FieldStatus,
    ManufacturerCandidate,
    ManufacturerFieldResult,
    MRPCandidate,
    MRPFieldResult,
    NetQuantityCandidate,
    NetQuantityFieldResult,
)


def _status_for(candidates: list) -> FieldStatus:
    if not candidates:
        return FieldStatus.NOT_FOUND
    if len(candidates) == 1:
        return FieldStatus.FOUND
        
    # Check for consensus among all candidates
    unique_values = set()
    for c in candidates:
        # Extract the core value depending on the candidate type
        val = getattr(c, "normalized_value", getattr(c, "value", getattr(c, "raw_text", None)))
        unique_values.add(val)
        
    if len(unique_values) == 1:
        # Multiple pieces of evidence, but they all agree on the exact same value.
        return FieldStatus.FOUND
        
    # Multiple distinct values found across images. This is a true conflict.
    return FieldStatus.MULTIPLE_CANDIDATES



def _dedupe(candidates: list) -> list:
    """Remove only exact duplicates. Never merge similar-but-different values."""
    seen: set[str] = set()
    unique = []
    for candidate in candidates:
        key = candidate.model_dump_json()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


class Aggregator:
    """Aggregates extractor output from all successfully processed images."""

    def aggregate(
        self,
        mrp_candidates: list[MRPCandidate],
        quantity_candidates: list[NetQuantityCandidate],
        date_candidates: list[DateDeclarationCandidate],
        manufacturer_candidates: list[ManufacturerCandidate],
    ) -> Fields:
        mrp = _dedupe(mrp_candidates)
        quantity = _dedupe(quantity_candidates)
        dates = _dedupe(date_candidates)
        manufacturer = _dedupe(manufacturer_candidates)

        return Fields(
            mrp=MRPFieldResult(status=_status_for(mrp), candidates=mrp),
            net_quantity=NetQuantityFieldResult(status=_status_for(quantity), candidates=quantity),
            date_declarations=DateDeclarationsFieldResult(status=_status_for(dates), candidates=dates),
            manufacturer_declarations=ManufacturerFieldResult(
                status=_status_for(manufacturer), candidates=manufacturer
            ),
        )
