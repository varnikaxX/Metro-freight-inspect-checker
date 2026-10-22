"""MRP / price declaration extractor.

Detects common Indian MRP declarations (MRP, M.R.P., Maximum Retail
Price) alongside a currency-marked or plain numeric value. Raw OCR
text is always preserved verbatim; only normalized_value may apply a
narrow, context-justified digit correction.
"""
from __future__ import annotations

import re

from app.extractors.base import BaseExtractor
from app.models.ocr_document import OCRDocument, OCRLine
from app.models.response import Confidence, MRPCandidate
from app.utils.normalization import apply_digit_lookalike_correction, normalize_whitespace

_MRP_KEYWORD_RE = re.compile(
    r"(m\.?\s*r\.?\s*p\.?|maximum\s+retail\s+price)", re.IGNORECASE
)

# Digits are allowed to include common OCR digit-lookalike characters
# (O, o, I, l, S, B) since correction only happens after this pattern
# has already matched inside a strong currency context.
_PRICE_PATTERN_RE = re.compile(
    r"(?:rs\.?|inr|₹)\s*([0-9OoIlSB]+(?:[.,][0-9OoIlSB]+)?)\s*(?:/-)?",
    re.IGNORECASE,
)

_BARE_NUMBER_RE = re.compile(r"\b([0-9]{1,6}(?:[.,][0-9]{1,2})?)\b")

_NEGATIVE_CONTEXT_RE = re.compile(
    r"\b(discount|cashback|off|save|promo|only)\b", 
    re.IGNORECASE
)


def _clean_number_token(token: str) -> str:
    return token.replace(",", "")


def _try_parse_price(token: str) -> float | None:
    corrected = apply_digit_lookalike_correction(_clean_number_token(token))
    try:
        return float(corrected)
    except ValueError:
        return None


class MRPExtractor(BaseExtractor):
    """Extracts Maximum Retail Price declarations from OCR text."""

    field_name = "mrp"

    def extract(self, document: OCRDocument, source_image_id: str) -> list[MRPCandidate]:
        candidates = self._extract_from_lines(document.lines, source_image_id)
        if not candidates:
            candidates = self._extract_from_full_text(document.full_text, source_image_id)
        return self._deduplicate(candidates)

    def _extract_from_lines(self, lines: list[OCRLine], source_image_id: str) -> list[MRPCandidate]:
        found: list[MRPCandidate] = []
        for index, line in enumerate(lines):
            text = line.text
            if not _MRP_KEYWORD_RE.search(text):
                continue

            price_match = _PRICE_PATTERN_RE.search(text)
            search_scope = text
            same_line = True

            if not price_match and index + 1 < len(lines):
                # Nearby-line fallback: keyword on one line, value on the next.
                next_text = lines[index + 1].text
                price_match = _PRICE_PATTERN_RE.search(next_text)
                if price_match:
                    search_scope = next_text
                    same_line = False

            if not price_match:
                # Keyword present but no currency-marked number nearby; try
                # a bare number on the same line as weaker evidence.
                bare_match = _BARE_NUMBER_RE.search(text)
                if bare_match:
                    value = _try_parse_price(bare_match.group(1))
                    found.append(
                        MRPCandidate(
                            raw_text=normalize_whitespace(text),
                            normalized_value=value,
                            currency="INR",
                            confidence=Confidence.MEDIUM,
                            source_image_id=source_image_id,
                            bounding_box=line.bounding_box,
                        )
                    )
                continue

            value = _try_parse_price(price_match.group(1))
            confidence = Confidence.HIGH if same_line else Confidence.MEDIUM
            found.append(
                MRPCandidate(
                    raw_text=normalize_whitespace(search_scope),
                    normalized_value=value,
                    currency="INR",
                    confidence=confidence,
                    source_image_id=source_image_id,
                    bounding_box=line.bounding_box if same_line else None,
                )
            )
        return found

    def _extract_from_full_text(self, full_text: str, source_image_id: str) -> list[MRPCandidate]:
        found: list[MRPCandidate] = []
        for match in _PRICE_PATTERN_RE.finditer(full_text):
            value = _try_parse_price(match.group(1))
            # Expand the snippet slightly to catch surrounding context
            snippet = normalize_whitespace(full_text[max(0, match.start() - 30): match.end() + 15])
            
            # Reject if it's clearly a discount or promotional price
            if _NEGATIVE_CONTEXT_RE.search(snippet):
                continue
                
            found.append(
                MRPCandidate(
                    raw_text=snippet,
                    normalized_value=value,
                    currency="INR",
                    confidence=Confidence.LOW,
                    source_image_id=source_image_id,
                    bounding_box=None,
                )
            )
        return found

    def _deduplicate(self, candidates: list[MRPCandidate]) -> list[MRPCandidate]:
        seen: set[tuple[str, float | None]] = set()
        unique: list[MRPCandidate] = []
        for candidate in candidates:
            key = (candidate.raw_text, candidate.normalized_value)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
