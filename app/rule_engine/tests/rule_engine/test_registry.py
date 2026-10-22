from __future__ import annotations

import json

import pytest

from app.rule_engine.registry import RuleRegistry, RuleSetValidationError


def test_ruleset_loading():
    """#17: Ruleset loading."""
    registry = RuleRegistry()
    assert registry.ruleset_id == "PACKAGED_COMMODITY"
    assert registry.version == "1.0.0"
    assert len(registry.rules) > 0
    assert all(r.rule_id for r in registry.rules)


def test_rules_for_field_filters_correctly():
    registry = RuleRegistry()
    mrp_rules = registry.rules_for_field("mrp")
    assert all(r.field == "mrp" for r in mrp_rules)
    assert any(r.rule_id == "MRP-001" for r in mrp_rules)


@pytest.mark.parametrize(
    "broken_ruleset",
    [
        {"version": "1.0.0", "rules": []},  # missing ruleset_id
        {"ruleset_id": "X", "rules": []},  # missing version
        {"ruleset_id": "X", "version": "1.0.0"},  # missing rules
        {"ruleset_id": "X", "version": "1.0.0", "rules": "not-a-list"},
        {
            "ruleset_id": "X",
            "version": "1.0.0",
            "rules": [{"rule_id": "R-1", "field": "not_a_real_field", "type": "PRESENCE", "severity": "HIGH", "message": "m"}],
        },
        {
            "ruleset_id": "X",
            "version": "1.0.0",
            "rules": [{"rule_id": "R-1", "field": "mrp", "type": "BOGUS_TYPE", "severity": "HIGH", "message": "m"}],
        },
        {
            "ruleset_id": "X",
            "version": "1.0.0",
            "rules": [
                {"rule_id": "R-1", "field": "mrp", "type": "PRESENCE", "severity": "HIGH", "message": "m"},
                {"rule_id": "R-1", "field": "mrp", "type": "PRESENCE", "severity": "HIGH", "message": "dup"},
            ],
        },
    ],
)
def test_invalid_ruleset_or_schema_rejected(tmp_path, broken_ruleset):
    """#18: Invalid ruleset/schema is rejected with a clear error."""
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(broken_ruleset))

    with pytest.raises(RuleSetValidationError):
        RuleRegistry(path)


def test_invalid_json_rejected(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{ not valid json")
    with pytest.raises(RuleSetValidationError):
        RuleRegistry(path)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(RuleSetValidationError):
        RuleRegistry(tmp_path / "does_not_exist.json")
