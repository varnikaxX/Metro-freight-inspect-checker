import os

from backend.services.compliance import run_compliance_check


def values(text):
    fields, _ = run_compliance_check(text)
    return {field["field_name"]: field["field_value"] for field in fields}


def test_mrp_uses_value_near_label_and_rejects_unit_price():
    result = values("Nutrition: 0.62/g\nM.R.P. ₹\n49.00\nSaturated fat 6.6 g")
    assert result["MRP"] == "₹49.00"


def test_mrp_comma_decimal_normalizes_with_evidence():
    fields, _ = run_compliance_check("M.R.P. 49,00")
    mrp = next(field for field in fields if field["field_name"] == "MRP")
    assert mrp["field_value"] == "₹49.00"
    assert mrp["source_line"] == "M.R.P. 49,00"


def test_net_quantity_uses_declaration_not_nutrition_grams():
    result = values("Nutrition facts: 14 g saturated content\nNET WEIGHT\n79 g")
    assert result["NET_QUANTITY"] == "79 g"


def test_manufacturing_date_does_not_use_use_by_date():
    result = values("DATE OF MANUFACTURE\n\nUSE BY DATE\n20/03/2027")
    assert result["MFG_DATE"] is None


def test_mrp_label_forms():
    for label in ("₹", "Rs.", "MRP", "M.R.P."):
        result = values(f"{label} 49.00")
        assert result["MRP"] == "₹49.00", label


def test_quantity_formats():
    for quantity in ("500g", "500 g", "0.5 kg", "200 ml"):
        result = values(f"NET CONTENT {quantity}")
        assert result["NET_QUANTITY"] == {"500g": "500 g", "500 g": "500 g", "0.5 kg": "0.5 kg", "200 ml": "200 ml"}[quantity]


def test_uncertain_values_stay_missing():
    result = values("M.R.P.\nSaturated fat 0.62/g\nDATE OF MANUFACTURE\nUSE BY 20/03/2027")
    assert result["MRP"] is None
    assert result["MFG_DATE"] is None


def test_ocr_line_order_is_preserved():
    ocr = {"lines": [{"text": "NET WEIGHT", "confidence": 0.9}, {"text": "79 g", "confidence": 0.9}]}
    result = values(ocr)
    assert result["NET_QUANTITY"] == "79 g"


def test_public_field_shape_is_unchanged():
    fields, violations = run_compliance_check("MRP ₹49.00")
    assert {"field_name", "field_value", "is_present"}.issubset(fields[0])
    assert all(set(violation).issuperset({"rule_code", "description"}) for violation in violations)


def test_empty_ocr_is_review_not_violation():
    fields, violations = run_compliance_check("")
    assert all(field["verification_state"] == "not_detected_needs_review" for field in fields if field["field_name"] != "COUNTRY_OF_ORIGIN")
    assert violations == []


def test_country_of_origin_is_conditional_without_import_indicator():
    fields, violations = run_compliance_check("Potato chips\nMRP ₹79")
    country = next(field for field in fields if field["field_name"] == "COUNTRY_OF_ORIGIN")
    assert country["verification_state"] == "not_assessed"
    assert not any("COUNTRY_OF_ORIGIN" in violation["rule_code"] for violation in violations)


def test_real_chips_label_strategy_comparison():
    """Print observed strategy output without inventing OCR success."""
    from pathlib import Path
    from backend.services import ocr

    image_path = Path(__file__).resolve().parents[1] / "trap_label.jpg"
    if not image_path.is_file():
        return
    original = os.environ.get("OCR_STRATEGY")
    rows = []
    try:
        for strategy in ("fast", "hybrid", "legacy"):
            os.environ["OCR_STRATEGY"] = strategy
            ocr.OCR_STRATEGY = strategy
            result = ocr.extract_text_from_image(image_path.read_bytes())
            fields, _ = run_compliance_check(result)
            by_name = {field["field_name"]: field for field in fields}
            rows.append((strategy, by_name["MRP"]["field_value"], by_name["NET_QUANTITY"]["field_value"]))
    finally:
        if original is None:
            os.environ.pop("OCR_STRATEGY", None)
        else:
            os.environ["OCR_STRATEGY"] = original
    print("strategy | MRP | NET_QUANTITY")
    for row in rows:
        print(" | ".join(str(value) for value in row))
