"""Tests for field extractors."""
from __future__ import annotations

from app.extractors.dates import DateExtractor
from app.extractors.manufacturer import ManufacturerExtractor
from app.extractors.price import MRPExtractor
from app.extractors.quantity import QuantityExtractor
from tests.fixtures.fake_provider import document_from_lines


def test_mrp_simple_rupee_symbol():
    document = document_from_lines(["MRP ₹50"])
    candidates = MRPExtractor().extract(document, "front")
    assert any(c.normalized_value == 50 for c in candidates)
    assert all(c.confidence.value == "HIGH" for c in candidates if c.normalized_value == 50)


def test_mrp_rs_with_slash():
    document = document_from_lines(["MRP Rs. 100/-"])
    candidates = MRPExtractor().extract(document, "front")
    assert any(c.normalized_value == 100 for c in candidates)


def test_mrp_digit_lookalike_with_strong_context():
    document = document_from_lines(["M.R.P ₹5O"])
    candidates = MRPExtractor().extract(document, "front")
    assert candidates, "expected at least one MRP candidate"
    top = candidates[0]
    assert top.raw_text == "M.R.P ₹5O"  # raw text must be preserved verbatim
    assert top.normalized_value == 50  # context-corrected value


def test_quantity_grams():
    document = document_from_lines(["Net Wt. 500g"])
    candidates = QuantityExtractor().extract(document, "back")
    assert any(c.value == 500 and c.unit == "g" for c in candidates)


def test_quantity_kg():
    document = document_from_lines(["1 kg"])
    candidates = QuantityExtractor().extract(document, "back")
    assert any(c.value == 1 and c.unit == "kg" for c in candidates)


def test_quantity_ml():
    document = document_from_lines(["250 ml"])
    candidates = QuantityExtractor().extract(document, "back")
    assert any(c.value == 250 and c.unit == "ml" for c in candidates)


def test_quantity_litre_short_form():
    document = document_from_lines(["1 L"])
    candidates = QuantityExtractor().extract(document, "back")
    assert any(c.value == 1 and c.unit == "l" for c in candidates)


def test_date_mfd_month_year():
    document = document_from_lines(["MFD:", "AUG 2026"])
    candidates = DateExtractor().extract(document, "back")

    matches = [c for c in candidates if c.label == "MFD"]

    assert matches
    assert any(
        c.raw_value == "AUG 2026"
        and c.normalized_value == "2026-08"
        for c in matches
    )


def test_date_best_before_value_on_next_line():
    document = document_from_lines(["BEST BEFORE:", "12 MONTHS"])
    candidates = DateExtractor().extract(document, "back")

    matches = [c for c in candidates if c.label == "BEST_BEFORE"]

    assert matches
    assert any(
        c.raw_value == "12 MONTHS"
        and c.normalized_value is None
        and c.declaration_type == "duration"
        for c in matches
    )


def test_date_does_not_use_unrelated_next_line():
    document = document_from_lines(["MFD:", "Ingredients: Sugar, Milk"])
    candidates = DateExtractor().extract(document, "back")

    matches = [c for c in candidates if c.label == "MFD"]

    assert matches
    assert matches[0].normalized_value is None
    assert matches[0].raw_value == "MFD:"
    document = document_from_lines(["MFD AUG 2026"])
    candidates = DateExtractor().extract(document, "back")
    assert any(c.label == "MFD" and c.normalized_value == "2026-08" for c in candidates)


def test_date_pkd_numeric_short_year():
    document = document_from_lines(["PKD 08/25"])
    candidates = DateExtractor().extract(document, "back")
    assert any(c.label == "PKD" and c.normalized_value == "2025-08" for c in candidates)


def test_date_exp_numeric_full_year():
    document = document_from_lines(["EXP 12/2026"])
    candidates = DateExtractor().extract(document, "back")
    assert any(c.label == "EXP" and c.normalized_value == "2026-12" for c in candidates)


def test_date_best_before_duration_not_invented():
    document = document_from_lines(["BEST BEFORE 12 MONTHS"])
    candidates = DateExtractor().extract(document, "back")
    matches = [c for c in candidates if c.label == "BEST_BEFORE"]
    assert matches
    assert matches[0].normalized_value is None
    assert matches[0].declaration_type == "duration"


def test_date_ambiguous_three_part_date_not_normalized():
    document = document_from_lines(["MFD 08/09/25"])
    candidates = DateExtractor().extract(document, "back")
    matches = [c for c in candidates if c.label == "MFD"]
    assert matches
    assert matches[0].normalized_value is None


def test_manufacturer_multiline_block():
    document = document_from_lines(["Manufactured by:", "ABC Foods Pvt Ltd", "Mumbai, Maharashtra"])
    candidates = ManufacturerExtractor().extract(document, "back")
    assert any(
        c.label == "MANUFACTURED_BY" and "ABC Foods Pvt Ltd" in c.raw_text and "Mumbai" in c.raw_text
        for c in candidates
    )
