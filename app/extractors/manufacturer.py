"""Manufacturer / packer declaration extractor.

Detects manufacturer/packer/marketer/importer labels and captures the
surrounding text block as evidence. No attempt is made to parse Indian
addresses or to judge legal sufficiency of the declaration.
"""
from __future__ import annotations

import re

from app.extractors.base import BaseExtractor
from app.models.ocr_document import OCRDocument
from app.models.response import Confidence, ManufacturerCandidate
from app.utils.normalization import normalize_whitespace

_LABEL_PATTERNS: dict[str, re.Pattern[str]] = {
    "MANUFACTURED_BY": re.compile(r"\bmanufactured\s+by\b|\bmanufacturer\b", re.IGNORECASE),
    "PACKED_BY": re.compile(r"\bpacked\s+by\b|\bpacker\b", re.IGNORECASE),
    "MARKETED_BY": re.compile(r"\bmarketed\s+by\b", re.IGNORECASE),
    "IMPORTED_BY": re.compile(r"\bimported\s+by\b", re.IGNORECASE),
}

# Stop reading if we hit another label or a completely unrelated declaration
_STOP_PATTERN = re.compile(
    r"\b(manufactured\s+by|marketed\s+by|packed\s+by|imported\s+by|mrp|rs\.?|₹|net\s+wt|net\s+weight|best\s+before|mfd\.?|pkd\.?|exp\.?)\b",
    re.IGNORECASE
)

# How many following lines to capture as evidence when the label line
# itself has little or no remaining text (e.g. "Manufactured by:").
_MAX_FOLLOWING_LINES = 2
_MIN_SAME_LINE_LENGTH = 3


class ManufacturerExtractor(BaseExtractor):
    """Extracts manufacturer/packer/marketer/importer declarations."""

    field_name = "manufacturer_declarations"

    def extract(self, document: OCRDocument, source_image_id: str) -> list[ManufacturerCandidate]:
        candidates: list[ManufacturerCandidate] = []
        lines = document.lines
        for index, line in enumerate(lines):
            for label, pattern in _LABEL_PATTERNS.items():
                match = pattern.search(line.text)
                if not match:
                    continue

                same_line_remainder = normalize_whitespace(line.text[match.end():].lstrip(" :.-"))
                
                # FIX B: Truncate if it bleeds into another declaration in the same paragraph
                stop_match = _STOP_PATTERN.search(same_line_remainder)
                if stop_match:
                    same_line_remainder = normalize_whitespace(same_line_remainder[:stop_match.start()].rstrip(" :.-"))

                text_parts = [same_line_remainder] if same_line_remainder else []

                if len(same_line_remainder) < _MIN_SAME_LINE_LENGTH:
                    # The label line has little/no content after it; pull in following lines
                    for offset in range(1, _MAX_FOLLOWING_LINES + 1):
                        if index + offset < len(lines):
                            next_text = lines[index + offset].text
                            
                            # FIX A: Stop appending if the next paragraph is clearly unrelated
                            if _STOP_PATTERN.search(next_text):
                                break
                                
                            text_parts.append(next_text)

                raw_text = normalize_whitespace(" ".join(part for part in text_parts if part))
                if not raw_text:
                    raw_text = normalize_whitespace(line.text)

                confidence = Confidence.HIGH if text_parts else Confidence.MEDIUM

                candidates.append(
                    ManufacturerCandidate(
                        label=label,
                        raw_text=raw_text,
                        confidence=confidence,
                        source_image_id=source_image_id,
                        bounding_box=line.bounding_box,
                    )
                )
        return self._deduplicate(candidates)

    def _deduplicate(self, candidates: list[ManufacturerCandidate]) -> list[ManufacturerCandidate]:
        seen: set[tuple[str, str]] = set()
        unique: list[ManufacturerCandidate] = []
        for candidate in candidates:
            key = (candidate.label, candidate.raw_text)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique