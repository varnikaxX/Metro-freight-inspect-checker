"""Rule registry: loads ruleset.json, validates its structure, and
exposes rules to the evaluator.

Adding, removing, or changing a compliance rule should mean editing
``rules/ruleset.json`` -- NOT editing this file or engine.py.

Validation note: this uses a small hand-written structural validator
(``_validate_structure``) rather than adding a ``jsonschema`` package
dependency, since that library's presence in this project was not
confirmed. ``rules/schema.json`` is still shipped as the authoritative,
tool-readable description of the expected shape -- if ``jsonschema`` IS
already a project dependency, swapping the body of
``_validate_structure`` for ``jsonschema.validate(data, schema)`` is a
one-function change.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.rule_engine.models import Rule

_DEFAULT_RULESET_PATH = Path(__file__).parent / "rules" / "ruleset.json"
_DEFAULT_SCHEMA_PATH = Path(__file__).parent / "rules" / "schema.json"

_VALID_FIELDS = {"mrp", "net_quantity", "date_declarations", "manufacturer_declarations"}
_VALID_TYPES = {"PRESENCE", "VALUE", "FORMAT", "CROSS_FIELD"}
_VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


class RuleSetValidationError(ValueError):
    """Raised when ruleset.json fails structural validation."""


def _validate_structure(data: dict) -> None:
    if not isinstance(data, dict):
        raise RuleSetValidationError("Ruleset root must be a JSON object.")

    for key in ("ruleset_id", "version", "rules"):
        if key not in data:
            raise RuleSetValidationError(f"Ruleset is missing required key: '{key}'.")

    if not isinstance(data["ruleset_id"], str) or not data["ruleset_id"]:
        raise RuleSetValidationError("'ruleset_id' must be a non-empty string.")
    if not isinstance(data["version"], str) or not data["version"]:
        raise RuleSetValidationError("'version' must be a non-empty string.")
    if not isinstance(data["rules"], list):
        raise RuleSetValidationError("'rules' must be a JSON array.")

    seen_ids: set[str] = set()
    for index, rule in enumerate(data["rules"]):
        if not isinstance(rule, dict):
            raise RuleSetValidationError(f"rules[{index}] must be a JSON object.")

        for key in ("rule_id", "field", "type", "severity", "message"):
            if key not in rule:
                raise RuleSetValidationError(f"rules[{index}] is missing required key: '{key}'.")

        rule_id = rule["rule_id"]
        if not isinstance(rule_id, str) or not rule_id:
            raise RuleSetValidationError(f"rules[{index}].rule_id must be a non-empty string.")
        if rule_id in seen_ids:
            raise RuleSetValidationError(f"Duplicate rule_id found: '{rule_id}'.")
        seen_ids.add(rule_id)

        if rule["field"] not in _VALID_FIELDS:
            raise RuleSetValidationError(
                f"rules[{index}] ('{rule_id}') has unknown field '{rule['field']}'. "
                f"Expected one of {sorted(_VALID_FIELDS)}."
            )
        if rule["type"] not in _VALID_TYPES:
            raise RuleSetValidationError(
                f"rules[{index}] ('{rule_id}') has unknown type '{rule['type']}'. "
                f"Expected one of {sorted(_VALID_TYPES)}."
            )
        if rule["severity"] not in _VALID_SEVERITIES:
            raise RuleSetValidationError(
                f"rules[{index}] ('{rule_id}') has unknown severity '{rule['severity']}'. "
                f"Expected one of {sorted(_VALID_SEVERITIES)}."
            )
        if not isinstance(rule["message"], str) or not rule["message"]:
            raise RuleSetValidationError(f"rules[{index}] ('{rule_id}').message must be a non-empty string.")
        if "params" in rule and not isinstance(rule["params"], dict):
            raise RuleSetValidationError(f"rules[{index}] ('{rule_id}').params must be a JSON object if present.")


class RuleRegistry:
    """Loads, validates, and exposes a versioned ruleset."""

    def __init__(self, ruleset_path: Path | str = _DEFAULT_RULESET_PATH) -> None:
        self._ruleset_path = Path(ruleset_path)
        self.ruleset_id: str
        self.version: str
        self._rules: list[Rule]
        self._load()

    def _load(self) -> None:
        try:
            raw = self._ruleset_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuleSetValidationError(f"Could not read ruleset file: {self._ruleset_path}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuleSetValidationError(f"Ruleset file is not valid JSON: {exc}") from exc

        _validate_structure(data)

        try:
            self._rules = [Rule.model_validate(r) for r in data["rules"]]
        except ValidationError as exc:  # pragma: no cover - _validate_structure catches these first
            raise RuleSetValidationError(f"Ruleset failed model validation: {exc}") from exc

        self.ruleset_id = data["ruleset_id"]
        self.version = data["version"]

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules)

    def rules_for_field(self, field_name: str) -> list[Rule]:
        return [r for r in self._rules if r.field == field_name]
