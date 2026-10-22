"""Rule Engine module.

Public entry point: ``app.rule_engine.engine.RuleEngine``.

    from app.rule_engine.engine import RuleEngine
    engine = RuleEngine()
    compliance_response = engine.evaluate(scan_response)

This module is intentionally isolated from the OCR pipeline internals.
See ``adapter.py`` for the only boundary crossing.
"""
