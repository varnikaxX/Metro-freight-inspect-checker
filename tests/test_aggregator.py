"""Tests for multi-image aggregation."""
from __future__ import annotations

from app.models.response import Confidence, FieldStatus, MRPCandidate, NetQuantityCandidate
from app.services.aggregator import Aggregator


def _mrp(value: float, image_id: str) -> MRPCandidate:
    return MRPCandidate(
        raw_text=f"MRP {value}",
        normalized_value=value,
        currency="INR",
        confidence=Confidence.HIGH,
        source_image_id=image_id,
    )


def _quantity(value: float, unit: str, image_id: str) -> NetQuantityCandidate:
    return NetQuantityCandidate(
        raw_text=f"{value}{unit}",
        value=value,
        unit=unit,
        confidence=Confidence.HIGH,
        source_image_id=image_id,
    )


def test_aggregation_combines_candidates_from_different_images():
    aggregator = Aggregator()
    fields = aggregator.aggregate(
        mrp_candidates=[_mrp(50, "front")],
        quantity_candidates=[_quantity(500, "g", "back")],
        date_candidates=[],
        manufacturer_candidates=[],
    )
    assert fields.mrp.status == FieldStatus.FOUND
    assert fields.net_quantity.status == FieldStatus.FOUND
    assert fields.mrp.candidates[0].source_image_id == "front"
    assert fields.net_quantity.candidates[0].source_image_id == "back"


def test_conflicting_mrp_candidates_are_both_preserved():
    aggregator = Aggregator()
    fields = aggregator.aggregate(
        mrp_candidates=[_mrp(50, "front"), _mrp(60, "back")],
        quantity_candidates=[],
        date_candidates=[],
        manufacturer_candidates=[],
    )
    assert fields.mrp.status == FieldStatus.MULTIPLE_CANDIDATES
    values = {c.normalized_value for c in fields.mrp.candidates}
    assert values == {50, 60}


def test_exact_duplicate_candidates_are_deduplicated():
    aggregator = Aggregator()
    fields = aggregator.aggregate(
        mrp_candidates=[_mrp(50, "front"), _mrp(50, "front")],
        quantity_candidates=[],
        date_candidates=[],
        manufacturer_candidates=[],
    )
    assert len(fields.mrp.candidates) == 1


def test_not_found_status_when_no_candidates():
    aggregator = Aggregator()
    fields = aggregator.aggregate(
        mrp_candidates=[],
        quantity_candidates=[],
        date_candidates=[],
        manufacturer_candidates=[],
    )
    assert fields.mrp.status == FieldStatus.NOT_FOUND
    assert fields.net_quantity.status == FieldStatus.NOT_FOUND
