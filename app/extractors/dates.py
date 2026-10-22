"""Date declaration extractor.

Extracts manufacturing/packing/expiry/best-before declarations. This
module ONLY extracts and preserves declarations -- it never determines
legal date validity or invents missing information.
"""
from __future__ import annotations

import re

from app.extractors.base import BaseExtractor
from app.models.ocr_document import OCRDocument, OCRLine
from app.models.response import Confidence, DateDeclarationCandidate
from app.utils.normalization import normalize_month_name, normalize_whitespace

_LABEL_PATTERNS: dict[str, re.Pattern[str]] = {
    "MFD": re.compile(r"\b(mfd|mfg|manufactured|manufacturing\s+date)\b", re.IGNORECASE),
    "PKD": re.compile(r"\b(pkd|packed\s+on|packing\s+date)\b", re.IGNORECASE),
    "EXP": re.compile(r"\b(exp|expiry)\b", re.IGNORECASE),
    "BEST_BEFORE": re.compile(r"\bbest\s+before\b", re.IGNORECASE),
}

_MONTH_YEAR_RE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{4})\b",
    re.IGNORECASE,
)

_NUMERIC_MM_YYYY_RE = re.compile(r"\b(\d{1,2})\s*/\s*(\d{4})\b")
_NUMERIC_MM_YY_RE = re.compile(r"\b(\d{1,2})\s*/\s*(\d{2})\b(?!\d)")
_THREE_PART_DATE_RE = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})\b")
_DURATION_RE = re.compile(r"\b(\d{1,3})\s*(days?|months?|years?)\b", re.IGNORECASE)


def _extract_value_after_label(text: str, label_match: re.Match[str]) -> str:
    remainder = text[label_match.end():]
    remainder = remainder.lstrip(" :.-")
    return normalize_whitespace(remainder) or normalize_whitespace(text)


def _normalize_date_value(raw_value: str) -> tuple[str | None, str]:
    """Return (normalized_value, declaration_type). Never guesses."""

    if _THREE_PART_DATE_RE.search(raw_value):
        # Three numeric components are ambiguous (DD/MM/YY vs MM/DD/YY) --
        # never guess the format.
        return None, "date"

    if _DURATION_RE.search(raw_value):
        return None, "duration"

    month_year_match = _MONTH_YEAR_RE.search(raw_value)
    if month_year_match:
        month = normalize_month_name(month_year_match.group(1))
        year = month_year_match.group(2)
        if month:
            return f"{year}-{month}", "date"

    mm_yyyy_match = _NUMERIC_MM_YYYY_RE.search(raw_value)
    if mm_yyyy_match:
        month, year = mm_yyyy_match.group(1), mm_yyyy_match.group(2)
        if 1 <= int(month) <= 12:
            return f"{year}-{int(month):02d}", "date"

    mm_yy_match = _NUMERIC_MM_YY_RE.search(raw_value)
    if mm_yy_match:
        month, year = mm_yy_match.group(1), mm_yy_match.group(2)
        if 1 <= int(month) <= 12:
            return f"20{year}-{int(month):02d}", "date"

    return None, "unknown"


class DateExtractor(BaseExtractor):
    field_name = "date_declarations"

    def extract(
        self,
        document: OCRDocument,
        source_image_id: str,
    ) -> list[DateDeclarationCandidate]:
        candidates: list[DateDeclarationCandidate] = []

        for index, line in enumerate(document.lines):
            next_line = (
                document.lines[index + 1]
                if index + 1 < len(document.lines)
                else None
            )
            candidates.extend(
                self._extract_from_line(line, source_image_id, next_line)
            )

        return self._deduplicate(candidates)

    def _extract_from_line(
        self,
        line: OCRLine,
        source_image_id: str,
        next_line: OCRLine | None = None,
    ) -> list[DateDeclarationCandidate]:
        found: list[DateDeclarationCandidate] = []
        text = line.text

        for label, pattern in _LABEL_PATTERNS.items():
            match = pattern.search(text)
            if not match:
                continue

            raw_value = _extract_value_after_label(text, match)

            if raw_value == normalize_whitespace(text) and next_line is not None:
                next_text = normalize_whitespace(next_line.text)

                if next_text and (
                    _MONTH_YEAR_RE.search(next_text)
                    or _NUMERIC_MM_YYYY_RE.search(next_text)
                    or _NUMERIC_MM_YY_RE.search(next_text)
                    or _THREE_PART_DATE_RE.search(next_text)
                    or _DURATION_RE.search(next_text)
                ):
                    raw_value = next_text

            normalized_value, declaration_type = _normalize_date_value(raw_value)
            confidence = Confidence.HIGH if normalized_value else Confidence.MEDIUM

            found.append(
                DateDeclarationCandidate(
                    label=label,
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    declaration_type=declaration_type,
                    confidence=confidence,
                    source_image_id=source_image_id,
                    bounding_box=line.bounding_box,
                )
            )

        return found

    def _deduplicate(self, candidates: list[DateDeclarationCandidate]) -> list[DateDeclarationCandidate]:
        seen: set[tuple[str, str]] = set()
        unique: list[DateDeclarationCandidate] = []
        for candidate in candidates:
            key = (candidate.label, candidate.raw_value)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
