"""
Tests for improved label-aware compliance extraction.

Uses live OCR data from actual chips packet to verify that labels and values
on separate lines are correctly extracted without false violations.
"""

from __future__ import annotations

from services.compliance import run_compliance_check


def test_live_chips_packet_ocr():
    """
    Test with actual live OCR from a chips packet.
    
    This OCR has labels (M.R.P., NET WEIGHT, DATE OF MANUFACTURE) on separate
    lines from their values. The extraction must find these values without
    creating false verified_missing violations.
    """
    # Live OCR text from actual chips packet scan
    live_ocr_text = """Potato Chips fried in Palmolein Oil. Potato
fried in Palmolein Oil have 14 g Saturated
content vs 7.4 g in Rice Bran Oil
SERVES PER PACK:
NET WEIGHT:
DATE OF
MANUFACTURE:
BATCH NO.:
USE BY DATE:
M.R.P.
(Inclusive of all taxes)
6.6
79 g
24/06/20265
N4 26 175
20/03/2027
49.00(USP Rs.0.62/g)
TOO YUMM! is a Trademark of Guiltfree"""

    fields, violations = run_compliance_check(live_ocr_text)

    # Build a dict for easier assertions
    field_dict = {f["field_name"]: f for f in fields}

    # --- MRP Assertions ---
    print("\n=== MRP Field ===")
    mrp_field = field_dict.get("MRP")
    print(f"MRP: {mrp_field}")
    assert mrp_field is not None, "MRP field must be present"
    assert mrp_field["field_value"] == "₹49.00", f"Expected MRP ₹49.00, got {mrp_field['field_value']}"
    assert mrp_field["is_present"] is True, "MRP should be marked as present"
    assert mrp_field["verification_state"] == "verified_present", f"Expected verified_present, got {mrp_field['verification_state']}"
    assert mrp_field["source_line"] == "49.00(USP Rs.0.62/g)", f"Expected source line with full raw text"
    
    # Verify no MRP violation was created
    mrp_violations = [v for v in violations if "MRP_MISSING" in v.get("rule_code", "")]
    assert len(mrp_violations) == 0, f"Should not create MRP violation, but got: {mrp_violations}"

    # --- NET_QUANTITY Assertions ---
    print("\n=== NET_QUANTITY Field ===")
    qty_field = field_dict.get("NET_QUANTITY")
    print(f"NET_QUANTITY: {qty_field}")
    assert qty_field is not None, "NET_QUANTITY field must be present"
    assert qty_field["field_value"] == "79 g", f"Expected NET_QUANTITY '79 g', got {qty_field['field_value']}"
    assert qty_field["is_present"] is True, "NET_QUANTITY should be marked as present"
    assert qty_field["verification_state"] == "verified_present", f"Expected verified_present, got {qty_field['verification_state']}"
    
    # Verify no NET_QUANTITY violation was created
    qty_violations = [v for v in violations if "NET_QTY_MISSING" in v.get("rule_code", "")]
    assert len(qty_violations) == 0, f"Should not create NET_QUANTITY violation, but got: {qty_violations}"

    # --- MFG_DATE Assertions ---
    print("\n=== MFG_DATE Field ===")
    mfg_field = field_dict.get("MFG_DATE")
    print(f"MFG_DATE: {mfg_field}")
    assert mfg_field is not None, "MFG_DATE field must be present"
    assert mfg_field["field_value"] == "24/06/20265", f"Expected '24/06/20265', got {mfg_field['field_value']}"
    # Date has 5-digit year, so should be not_detected_needs_review
    assert mfg_field["verification_state"] == "not_detected_needs_review", f"Expected not_detected_needs_review for 5-digit year, got {mfg_field['verification_state']}"
    assert mfg_field["candidate_status"] == "low_confidence_candidate", f"Expected low_confidence_candidate, got {mfg_field['candidate_status']}"
    
    # Verify no MFG_DATE violation was created (we explicitly exclude it from creating false violations)
    mfg_violations = [v for v in violations if "MFG_DATE_MISSING" in v.get("rule_code", "")]
    assert len(mfg_violations) == 0, f"Should not create MFG_DATE violation for plausible but invalid date, but got: {mfg_violations}"

    # --- COMMON_NAME Assertions ---
    print("\n=== COMMON_NAME Field ===")
    common_field = field_dict.get("COMMON_NAME")
    print(f"COMMON_NAME: {common_field}")
    assert common_field is not None, "COMMON_NAME field must be present"
    # Should extract "Potato Chips" from the first line
    assert "Potato" in common_field["field_value"] and "Chips" in common_field["field_value"], f"Expected 'Potato Chips', got {common_field['field_value']}"
    assert common_field["verification_state"] in ("verified_present", "not_detected_needs_review"), f"Expected verified_present or needs_review, got {common_field['verification_state']}"
    
    # --- Summary ---
    print("\n=== Summary ===")
    print(f"Total fields extracted: {len(fields)}")
    print(f"Total violations: {len(violations)}")
    for v in violations:
        print(f"  - {v['rule_code']}: {v['description'][:60]}...")
    
    # The main assertion: no false violations for fields we have reliable extraction for
    false_violation_codes = {
        "LMR_2011_R6_1_F_MRP_MISSING",
        "LMR_2011_R6_1_D_NET_QTY_MISSING",
        "LMR_2011_R6_1_E_MFG_DATE_MISSING",
    }
    violations_found = {v["rule_code"] for v in violations}
    false_violations = violations_found & false_violation_codes
    
    assert len(false_violations) == 0, f"Should not create false violations for extracted fields, but got: {false_violations}"
    
    print("\n✓ All assertions passed!")


def test_unit_price_rejection():
    """
    Verify that unit-price patterns like Rs.0.62/g are rejected as MRP values.
    """
    ocr_with_unit_price = """M.R.P.
49.00(USP Rs.0.62/g)"""

    fields, violations = run_compliance_check(ocr_with_unit_price)
    field_dict = {f["field_name"]: f for f in fields}

    mrp_field = field_dict.get("MRP")
    assert mrp_field is not None
    # Should still extract 49.00, not 0.62
    assert mrp_field["field_value"] == "₹49.00", f"Expected ₹49.00, got {mrp_field['field_value']}"
    print("✓ Unit-price rejection test passed")


def test_five_digit_year_rejection():
    """
    Verify that dates with 5-digit years are marked as low-confidence.
    """
    ocr_with_bad_date = """DATE OF MANUFACTURE:
24/06/20265"""

    fields, violations = run_compliance_check(ocr_with_bad_date)
    field_dict = {f["field_name"]: f for f in fields}

    mfg_field = field_dict.get("MFG_DATE")
    assert mfg_field is not None
    assert mfg_field["field_value"] == "24/06/20265"
    assert mfg_field["verification_state"] == "not_detected_needs_review", "5-digit year should be marked needs_review"
    assert mfg_field["candidate_status"] == "low_confidence_candidate"
    
    # Should NOT create a violation
    mfg_violations = [v for v in violations if "MFG_DATE_MISSING" in v.get("rule_code", "")]
    assert len(mfg_violations) == 0
    print("✓ Five-digit year rejection test passed")


def test_label_only_line_skipping():
    """
    Verify that label-only lines (like "(Inclusive of all taxes)") are skipped
    when looking for values on following lines.
    """
    ocr_with_label_separator = """M.R.P.
(Inclusive of all taxes)
49.00"""

    fields, violations = run_compliance_check(ocr_with_label_separator)
    field_dict = {f["field_name"]: f for f in fields}

    mrp_field = field_dict.get("MRP")
    assert mrp_field is not None
    # Should find 49.00 even though it's 2 lines after the label
    assert mrp_field["field_value"] == "₹49.00", f"Expected ₹49.00, got {mrp_field['field_value']}"
    assert mrp_field["verification_state"] == "verified_present"
    print("✓ Label-only line skipping test passed")


if __name__ == "__main__":
    test_live_chips_packet_ocr()
    test_unit_price_rejection()
    test_five_digit_year_rejection()
    test_label_only_line_skipping()
    print("\n✅ All tests passed!")
