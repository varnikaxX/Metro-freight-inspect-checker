"""Validators: reusable, deterministic rule-evaluation strategies.

Each validator implements one ``RuleType`` (PRESENCE, VALUE, FORMAT,
CROSS_FIELD). Dispatch from rule.type -> validator instance happens in
``dispatch()`` below rather than an if/elif chain in engine.py, so
adding a new validator type means adding a class + one registry entry
here, not editing the engine.
"""
from __future__ import annotations

from app.rule_engine.models import RuleType
from app.rule_engine.validators.base import Validator
from app.rule_engine.validators.cross_field import CrossFieldValidator
from app.rule_engine.validators.format import FormatValidator
from app.rule_engine.validators.presence import PresenceValidator
from app.rule_engine.validators.value import ValueValidator

_VALIDATORS: dict[RuleType, Validator] = {
    RuleType.PRESENCE: PresenceValidator(),
    RuleType.VALUE: ValueValidator(),
    RuleType.FORMAT: FormatValidator(),
    RuleType.CROSS_FIELD: CrossFieldValidator(),
}


def dispatch(rule_type: RuleType) -> Validator:
    try:
        return _VALIDATORS[rule_type]
    except KeyError as exc:  # pragma: no cover - guarded by schema validation in registry.py
        raise ValueError(f"No validator registered for rule type: {rule_type}") from exc


__all__ = ["dispatch", "Validator"]
