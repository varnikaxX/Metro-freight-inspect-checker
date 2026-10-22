"""Conservative normalization utilities.

These helpers never invent data. They only clean up formatting and
apply narrow, context-justified corrections explicitly requested by
extractors. Raw OCR text is always preserved separately by callers.
"""
from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")

MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "sept": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

# Characters commonly confused with digits by OCR. Only ever applied when
# an extractor has already established strong contextual justification
# (e.g. the token sits inside an already-matched price/quantity pattern).
_OCR_DIGIT_LOOKALIKES = {
    "O": "0", "o": "0",
    "I": "1", "l": "1",
    "S": "5",
    "B": "8",
}


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and trim."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_unit_spelling(unit: str) -> str:
    """Normalize obvious unit spelling variants to a canonical short form."""
    unit_lower = unit.strip().lower().rstrip(".")
    mapping = {
        "gram": "g", "grams": "g", "gm": "g", "gms": "g", "g": "g",
        "kilogram": "kg", "kilograms": "kg", "kg": "kg", "kgs": "kg",
        "millilitre": "ml", "milliliter": "ml", "millilitres": "ml",
        "milliliters": "ml", "ml": "ml",
        "litre": "l", "liter": "l", "litres": "l", "liters": "l", "l": "l",
    }
    return mapping.get(unit_lower, unit_lower)


def normalize_month_name(token: str) -> str | None:
    """Return a two-digit month string for a recognized month name/abbrev."""
    return MONTH_MAP.get(token.strip().lower())


def apply_digit_lookalike_correction(token: str) -> str:
    """Apply a narrow, context-justified O/I/S/B -> digit correction.

    Callers must only use this after confirming strong contextual
    evidence (e.g. the token sits inside an already-matched price or
    quantity pattern). This never touches raw_text -- only a derived
    normalized_value.
    """
    return "".join(_OCR_DIGIT_LOOKALIKES.get(ch, ch) for ch in token)


def normalize_currency_symbol(text: str) -> str:
    """Normalize obvious currency representations for matching purposes only."""
    replacements = {
        "Rs.": "₹",
        "Rs": "₹",
        "INR": "₹",
    }
    normalized = text
    for old, new in replacements.items():
        normalized = re.sub(rf"\b{re.escape(old)}\b", new, normalized, flags=re.IGNORECASE)
    return normalized
