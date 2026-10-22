"""Net quantity extractor.

Detects common net-quantity declarations (500g, 1kg, 250ml, 1L, 100
grams, etc.) with contextual keyword support (Net Wt, Net Weight, Net
Quantity, Quantity) plus a lower-confidence fallback for standalone
quantity patterns.
"""
from __future__ import annotations

import re

from app.extractors.base import BaseExtractor
from app.models.ocr_document import OCRDocument, OCRLine
from app.models.response import Confidence, NetQuantityCandidate
from app.utils.normalization import normalize_unit_spelling, normalize_whitespace

_QUANTITY_KEYWORD_RE = re.compile(
    r"(net\s*wt\.?|net\s+weight|net\s+quantity|quantity)", re.IGNORECASE
)
_QUANTITY_PATTERN_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*(kgs?|kilograms?|gms?|grams?|g|ml|millilitres?|milliliters?|"
    r"litres?|liters?|l)\b",
    re.IGNORECASE,
)

_NEGATIVE_CONTEXT_RE = re.compile(
    r"\b(per|nutritional?|nutrition|sugar|protein|fat|carbs|energy|calories|kcal|free|extra|contains|ingredients?)\b",
    re.IGNORECASE
)

class QuantityExtractor(BaseExtractor):
    """Extracts net quantity declarations from OCR text."""

    field_name = "net_quantity"

    def extract(self, document: OCRDocument, source_image_id: str) -> list[NetQuantityCandidate]:
        candidates = self._extract_from_lines(document.lines, source_image_id)
        if not candidates:
            candidates = self._extract_from_full_text(document.full_text, source_image_id)
        return self._deduplicate(candidates)

    def _extract_from_lines(self, lines: list[OCRLine], source_image_id: str) -> list[NetQuantityCandidate]:
        found: list[NetQuantityCandidate] = []
        for line in lines:
            text = line.text
            has_keyword = bool(_QUANTITY_KEYWORD_RE.search(text))
            has_negative = bool(_NEGATIVE_CONTEXT_RE.search(text))
            
            for match in _QUANTITY_PATTERN_RE.finditer(text):
                # Reject if there is no explicit quantity keyword but a distractor keyword is present
                if not has_keyword and has_negative:
                    continue
                    
                value = float(match.group(1))
                unit = normalize_unit_spelling(match.group(2))
                confidence = Confidence.HIGH if has_keyword else Confidence.MEDIUM
                found.append(
                    NetQuantityCandidate(
                        raw_text=normalize_whitespace(text),
                        value=value,
                        unit=unit,
                        confidence=confidence,
                        source_image_id=source_image_id,
                        bounding_box=line.bounding_box,
                    )
                )
        return found

    def _extract_from_full_text(self, full_text: str, source_image_id: str) -> list[NetQuantityCandidate]:
        found: list[NetQuantityCandidate] = []
        for match in _QUANTITY_PATTERN_RE.finditer(full_text):
            snippet = normalize_whitespace(full_text[max(0, match.start() - 25): match.end() + 15])
            
            # Reject if negative context is found nearby
            if _NEGATIVE_CONTEXT_RE.search(snippet):
                continue
                
            value = float(match.group(1))
            unit = normalize_unit_spelling(match.group(2))
            found.append(
                NetQuantityCandidate(
                    raw_text=snippet,
                    value=value,
                    unit=unit,
                    confidence=Confidence.LOW,
                    source_image_id=source_image_id,
                    bounding_box=None,
                )
            )
        return found
    
    
    def _deduplicate(self, candidates: list[NetQuantityCandidate]) -> list[NetQuantityCandidate]:
        seen: set[tuple[str, float | None, str | None]] = set()
        unique: list[NetQuantityCandidate] = []
        for candidate in candidates:
            key = (candidate.raw_text, candidate.value, candidate.unit)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
