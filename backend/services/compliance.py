"""Label-aware extraction for Legal Metrology declarations."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple

logger = logging.getLogger("compliance_service")

RULE_METADATA: Dict[str, Dict[str, str]] = {
    "MRP": {
        "rule_code": "LMR_2011_R6_1_F_MRP_MISSING",
        "description": "Maximum Retail Price (MRP) inclusive of all taxes is not declared on the package as required under Rule 6(1)(f).",
    },
    "NET_QUANTITY": {
        "rule_code": "LMR_2011_R6_1_D_NET_QTY_MISSING",
        "description": "Net quantity (in standard units of weight/measure/number) is not declared as required under Rule 6(1)(d).",
    },
    "MANUFACTURER_NAME": {
        "rule_code": "LMR_2011_R6_1_A_MFR_DETAILS_MISSING",
        "description": "Name and address of the manufacturer/packer/importer is not declared as required under Rule 6(1)(a).",
    },
    "CONSUMER_CARE": {
        "rule_code": "LMR_2011_R6_1_A_CONSUMER_CARE_MISSING",
        "description": "Consumer care / complaint contact details are not declared on the package.",
    },
    "MFG_DATE": {
        "rule_code": "LMR_2011_R6_1_E_MFG_DATE_MISSING",
        "description": "Month and year of manufacture/pre-packing/import is not declared as required under Rule 6(1)(e).",
    },
    "COUNTRY_OF_ORIGIN": {
        "rule_code": "LMR_2011_R6_1_COUNTRY_OF_ORIGIN_MISSING",
        "description": "Country of origin is not declared on the package (mandatory for imported goods).",
    },
    "COMMON_NAME": {
        "rule_code": "LMR_2011_R6_1_B_COMMON_NAME_MISSING",
        "description": "Common or generic name of the commodity is not declared as required under Rule 6(1)(b).",
    },
}

LABELS = {
    "MRP": re.compile(
        r"(?:\bm\s*\.?\s*r\s*\.?\s*p\s*\.?\b|maximum\s+retail\s+price|\brs\s*\.?|\binr\b|₹)",
        re.I,
    ),
    "NET_QUANTITY": re.compile(
        r"\bnet\s+(?:weight|wt|quantity|qty|content|contents?)\b",
        re.I,
    ),
    "MFG_DATE": re.compile(
        r"\b(?:date\s+of\s+(?:mfg|manufacture|packing)|mfg|mfd|manufacture|manufactured|pkd|packed\s+on)\b",
        re.I,
    ),
    "EXPIRY": re.compile(
        r"\b(?:use\s+by|expiry|exp\.?|best\s+before)\b",
        re.I,
    ),
    "COMMON_NAME": re.compile(
        r"\b(?:chips?|potato\s+chips?|snack|namkeen|biscuits?|wafers?)\b",
        re.I,
    ),
    "CONSUMER_CARE": re.compile(
        r"\b(?:customer|consumer)\s+care|\bcomplaints?\b|\b(?:contact|helpline)\b",
        re.I,
    ),
    "MANUFACTURER_NAME": re.compile(
        r"\b(?:manufactured|packed|packaged|imported)\s+by\b|\b(?:manufacturer|packer|importer)\b",
        re.I,
    ),
}

NUMBER = r"\d{1,4}(?:[.,]\d{1,3})?"
QUANTITY = re.compile(
    rf"(?<![\w/])({NUMBER})\s*(kg|g|gm|gms|grams?|ml|m[lL]|lit(?:re|er)s?|L)\b",
    re.I,
)
MONEY = re.compile(
    rf"(?<![\w/])(?:₹|rs\.?|inr)?\s*({NUMBER})(?!\s*/\s*g)(?!\s*(?:g|kg|ml)\b)",
    re.I,
)
DATE = re.compile(
    r"\b(?:"
    r"\d{1,2}\s*[/.-]\s*\d{1,2}\s*[/.-]\s*\d{2,5}"
    r"|\d{1,2}\s*[/.-]\s*\d{2,5}"
    r"|\d{1,2}\s+\d{1,2}\s+\d{2,5}"
    r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}"
    r")\b",
    re.I,
)
PHONE = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{9}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def normalize_ocr_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def clean_ocr_token(text: str) -> str:
    return normalize_ocr_text(text).strip(" :;|,-")


def _ordered_lines(
    ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if isinstance(ocr, str):
        return [
            {
                "text": clean_ocr_token(line),
                "raw_line_text": line,
                "confidence": 0.0,
                "line_number": i,
            }
            for i, line in enumerate(ocr.splitlines())
            if clean_ocr_token(line)
        ]

    if isinstance(ocr, dict):
        raw = ocr.get("lines") or [
            {
                "text": block.get("text", ""),
                "confidence": block.get("confidence", 0.0),
            }
            for block in ocr.get("blocks", [])
        ]
    else:
        raw = list(ocr)

    result: List[Dict[str, Any]] = []
    for i, line in enumerate(raw):
        raw_text = str(line.get("raw_line_text", line.get("text", "")))
        text = clean_ocr_token(str(line.get("text", "")))
        if text:
            result.append(
                {
                    **line,
                    "text": text,
                    "raw_line_text": raw_text,
                    "line_number": line.get("line_number", i),
                }
            )
    return result


def nearby_lines(
    lines: List[Dict[str, Any]], index: int, radius: int = 3
) -> List[Tuple[int, Dict[str, Any]]]:
    return [
        (candidate, lines[candidate])
        for candidate in range(index, min(len(lines), index + radius + 1))
    ]


def right_of_label(label_match: re.Match[str], text: str) -> str:
    return clean_ocr_token(text[label_match.end() :])


def value_after_label(
    lines: List[Dict[str, Any]],
    label: re.Pattern[str],
    value_pattern: re.Pattern[str],
    reject: re.Pattern[str] | None = None,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for index, line in enumerate(lines):
        match = label.search(line["text"])
        if not match:
            continue

        for distance, (_, nearby) in enumerate(nearby_lines(lines, index, 3)):
            fragment = (
                right_of_label(match, line["text"])
                if distance == 0
                else nearby["text"]
            )

            if reject and (reject.search(fragment) or reject.search(line["text"])):
                logger.debug("Rejected candidate %r: reject pattern", fragment)
                continue

            for value_match in value_pattern.finditer(fragment):
                candidates.append(
                    {
                        "value": clean_ocr_token(value_match.group(0)),
                        "raw_text": value_match.group(0),
                        "source_line": nearby.get(
                            "raw_line_text",
                            nearby["text"],
                        ),
                        "confidence": float(nearby.get("confidence", 0.0)),
                        "distance": distance,
                        "line": index + distance,
                    }
                )

    return candidates


def value_following_label(
    lines: List[Dict[str, Any]],
    label: re.Pattern[str],
    value_pattern: re.Pattern[str],
    reject: re.Pattern[str] | None = None,
    max_distance: int = 5,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for label_line_idx, line in enumerate(lines):
        match = label.search(line["text"])
        if not match:
            continue

        same_line_fragment = right_of_label(match, line["text"])
        if same_line_fragment:
            if not (
                reject
                and (
                    reject.search(same_line_fragment)
                    or reject.search(line["text"])
                )
            ):
                for value_match in value_pattern.finditer(same_line_fragment):
                    candidates.append(
                        {
                            "value": clean_ocr_token(value_match.group(0)),
                            "raw_text": value_match.group(0),
                            "source_line": line.get(
                                "raw_line_text",
                                line["text"],
                            ),
                            "confidence": float(line.get("confidence", 0.0)),
                            "distance": 0,
                            "line": label_line_idx,
                        }
                    )

        label_cluster_size = 0
        for offset in range(1, min(4, len(lines) - label_line_idx)):
            following_line = lines[label_line_idx + offset]
            if any(
                pattern.search(following_line["text"])
                for label_name, pattern in LABELS.items()
                if label_name not in {"EXPIRY"}
            ):
                label_cluster_size += 1
            else:
                break

        start_offset = label_cluster_size + 1

        for offset in range(
            label_cluster_size + 1,
            min(label_cluster_size + 3, len(lines) - label_line_idx),
        ):
            following_line = lines[label_line_idx + offset]
            following_text = following_line["text"]

            if (
                following_text.startswith("(")
                and following_text.endswith(")")
                and not value_pattern.search(following_text)
            ):
                start_offset = offset + 1
                continue
            break

        for offset in range(start_offset, max_distance + 1):
            if label_line_idx + offset >= len(lines):
                break

            following_line = lines[label_line_idx + offset]
            following_text = following_line["text"]

            has_other_label = any(
                pattern.search(following_text)
                for label_name, pattern in LABELS.items()
                if label_name not in {"MRP", "NET_QUANTITY", "MFG_DATE", "EXPIRY"}
            )
            has_our_pattern = bool(value_pattern.search(following_text))

            if has_other_label and not has_our_pattern:
                logger.debug(
                    "Skipping line %d (has declaration label, no value): %r",
                    label_line_idx + offset,
                    following_text,
                )
                continue

            if reject and reject.search(following_text):
                logger.debug(
                    "Rejected line %d by reject pattern: %r",
                    label_line_idx + offset,
                    following_text,
                )
                continue

            for value_match in value_pattern.finditer(following_text):
                candidates.append(
                    {
                        "value": clean_ocr_token(value_match.group(0)),
                        "raw_text": value_match.group(0),
                        "source_line": following_line.get(
                            "raw_line_text",
                            following_line["text"],
                        ),
                        "confidence": float(following_line.get("confidence", 0.0)),
                        "distance": offset,
                        "line": label_line_idx + offset,
                    }
                )

    return candidates


def candidate_score(candidate: Dict[str, Any]) -> float:
    return candidate.get("confidence", 0.0) + max(
        0,
        3 - candidate.get("distance", 3),
    ) * 0.2


def choose_highest_confidence_candidate(candidates: List[Dict[str, Any]]) -> str | None:
    if not candidates:
        return None

    selected = max(candidates, key=candidate_score)
    logger.debug("Candidates considered: %s; selected: %s", candidates, selected)
    return selected["value"]


def _choose_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not candidates:
        return None
    return max(candidates, key=candidate_score)


def _normalize_mrp_value(raw: str) -> str | None:
    match = re.search(r"\d+(?:[.,]\d+)?", raw)
    if not match:
        return None

    amount = float(match.group(0).replace(",", "."))
    return f"₹{amount:.2f}"


def _mrp_search_text(text: str) -> str:
    text = (text or "").replace("₹", " INR ")
    text = re.sub(r"\bR5\b", "RS", text, flags=re.I)
    text = re.sub(
        r"\b(?:M\s*\.\s*R\s*\.\s*P|M\s+R\s+P)\b",
        "MRP",
        text,
        flags=re.I,
    )
    return normalize_ocr_text(text)


def _normalize_quantity_value(raw: str) -> str | None:
    match = QUANTITY.search(raw)
    if not match:
        return None

    number = match.group(1).replace(",", ".")
    unit = match.group(2).lower()
    unit = {
        "gm": "g",
        "gms": "g",
        "gram": "g",
        "grams": "g",
        "millilitre": "ml",
        "millilitres": "ml",
        "litre": "l",
        "litres": "l",
        "liter": "l",
        "liters": "l",
    }.get(unit, unit)

    return f"{number} {unit}"


def _date_parts(value: str) -> List[int]:
    return [int(part) for part in re.findall(r"\d+", value or "")]


def _normalize_mfg_date_value(raw: str) -> Tuple[str | None, bool]:
    """
    Returns (normalized_date, was_ocr_repaired).

    A five-digit year can occur when OCR attaches one extra trailing digit,
    e.g. 24/06/20265. We safely repair only by taking the first four digits
    if that forms a valid calendar date.
    """
    raw = clean_ocr_token(raw)
    raw = re.sub(r"\s+", "", raw)

    numeric = re.search(
        r"(?P<day>\d{1,2})[./-](?P<month>\d{1,2})[./-](?P<year>\d{2,5})",
        raw,
    )

    if numeric:
        day = int(numeric.group("day"))
        month = int(numeric.group("month"))
        original_year = numeric.group("year")
        repaired = False

        if len(original_year) == 5:
            year_text = original_year[:4]
            repaired = True
        else:
            year_text = original_year

        year = int(year_text)
        actual_year = 2000 + year if len(year_text) == 2 else year

        try:
            datetime(actual_year, month, day)
        except ValueError:
            return None, False

        return f"{day:02d}/{month:02d}/{year_text}", repaired

    month_year = re.search(r"(?P<month>\d{1,2})[./-](?P<year>\d{2,5})", raw)
    if month_year:
        month = int(month_year.group("month"))
        original_year = month_year.group("year")
        repaired = False

        if len(original_year) == 5:
            year_text = original_year[:4]
            repaired = True
        else:
            year_text = original_year

        year = int(year_text)
        actual_year = 2000 + year if len(year_text) == 2 else year

        try:
            datetime(actual_year, month, 1)
        except ValueError:
            return None, False

        return f"{month:02d}/{year_text}", repaired

    return None, False


def _find_date_strings(text: str) -> List[str]:
    return [
        clean_ocr_token(match.group(0))
        for match in DATE.finditer(text or "")
    ]


def validated_field_count(
    ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]
) -> int:
    raw_full_text = ""
    if isinstance(ocr, dict):
        raw_full_text = str(ocr.get("full_text") or "")
    elif isinstance(ocr, str):
        raw_full_text = ocr

    lines = _ordered_lines(ocr)

    return sum(
        value is not None
        for value in (
            _extract_mrp(lines, raw_full_text),
            _extract_quantity(lines, raw_full_text),
            _extract_mfg_date(lines, raw_full_text),
        )
    )


def needs_fallback(ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]) -> bool:
    lines = _ordered_lines(ocr)

    reject = re.compile(
        r"/\s*g|saturated|calories|protein|carbohydrate|serving|cashback|discount|free",
        re.I,
    )

    mrp = _choose_candidate(value_after_label(lines, LABELS["MRP"], MONEY, reject))
    quantity = _choose_candidate(
        value_after_label(
            lines,
            LABELS["NET_QUANTITY"],
            QUANTITY,
            re.compile(
                r"nutrition|saturated|serving|calories|protein|carbohydrate",
                re.I,
            ),
        )
    )

    return quantity is None or mrp is None or float(mrp.get("confidence", 0.0)) < 0.65


def debug_candidate_summary(
    ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    lines = _ordered_lines(ocr)

    return {
        "mrp": value_after_label(
            lines,
            LABELS["MRP"],
            MONEY,
            re.compile(
                r"/\s*g|saturated|calories|protein|carbohydrate|serving",
                re.I,
            ),
        ),
        "net_quantity": value_after_label(
            lines,
            LABELS["NET_QUANTITY"],
            QUANTITY,
            re.compile(
                r"nutrition|saturated|serving|calories|protein|carbohydrate",
                re.I,
            ),
        ),
        "mfg_date": _valid_mfg_candidates(lines),
    }


def missing_high_value_fields(
    ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]
) -> List[str]:
    raw_full_text = ""
    if isinstance(ocr, dict):
        raw_full_text = str(ocr.get("full_text") or "")
    elif isinstance(ocr, str):
        raw_full_text = ocr

    lines = _ordered_lines(ocr)

    return [
        field
        for field, extractor in (
            ("MRP", lambda current_lines: _extract_mrp(current_lines, raw_full_text)),
            (
                "NET_QUANTITY",
                lambda current_lines: _extract_quantity(current_lines, raw_full_text),
            ),
            (
                "MFG_DATE",
                lambda current_lines: _extract_mfg_date(current_lines, raw_full_text),
            ),
        )
        if extractor(lines) is None
    ]


def _extract_quantity(
    lines: List[Dict[str, Any]],
    raw_full_text: str = "",
) -> str | None:
    return _extract_net_quantity(lines, raw_full_text)


def _extract_mrp(
    lines: List[Dict[str, Any]],
    raw_full_text: str = "",
) -> str | None:
    search_text = _mrp_search_text(
        raw_full_text or " ".join(line["text"] for line in lines)
    )

    explicit_pattern = re.compile(
        r"(?:\bMRP\b|\bmaximum\s+retail\s+price\b)"
        r"(?P<context>.{0,120}?)"
        r"(?:(?:INR|RS)\s*[:.]?\s*|₹\s*)?"
        r"(?P<amount>\d{1,5}(?:[.,]\d{1,2})?)"
        r"(?:\s*/\s*-)?",
        re.I,
    )

    nutrition_words = re.compile(
        r"energy|protein|carbohydrates?|sugar|fat|sodium|rda|nutrition|serving|expiry|use\s+by|best\s+before|batch\s+no",
        re.I,
    )

    for match in explicit_pattern.finditer(search_text):
        context = match.group("context")
        after = search_text[match.end() : match.end() + 16]

        if nutrition_words.search(context) or re.search(
            r"(?:/|per)\s*(?:g|kg|ml|l)\b|\d+(?:[.,]\d+)?\s*g\b",
            after,
            re.I,
        ):
            continue

        normalized = _normalize_mrp_value(match.group("amount"))
        if normalized:
            logger.info("MRP_EXTRACT method=explicit_label value=%s", normalized)
            logger.info(
                "MRP_SOURCE method=%s value=%r raw_has_mrp=%s",
                "explicit_label",
                normalized,
                bool(
                    re.search(
                        r"\bM\s*\.?\s*R\s*\.?\s*P\b|maximum\s+retail",
                        raw_full_text,
                        re.I,
                    )
                ),
            )
            return normalized

    if raw_full_text:
        usp_match = re.search(
            r"(?<!\d)(\d{1,5}(?:[.,]\d{1,2})?)\s*"
            r"\(\s*USP\s+Rs\.?\s*\d+(?:[.,]\d+)?\s*/\s*g\s*\)",
            raw_full_text,
            re.I,
        )
        if usp_match:
            normalized = _normalize_mrp_value(usp_match.group(1))
            if normalized:
                logger.info("MRP_EXTRACT method=fallback value=%s", normalized)
                return normalized

    all_text = " ".join(line.get("text", "") for line in lines)
    usp_match = re.search(
        r"(?<!\d)(\d{1,5}(?:[.,]\d{1,2})?)\s*"
        r"\(\s*USP\s+Rs\.?\s*\d+(?:[.,]\d+)?\s*/\s*g\s*\)",
        all_text,
        re.I,
    )

    if usp_match:
        normalized = _normalize_mrp_value(usp_match.group(1))
        if normalized:
            logger.info("MRP_EXTRACT method=fallback value=%s", normalized)
            return normalized

    candidates = value_following_label(
        lines,
        LABELS["MRP"],
        MONEY,
        re.compile(
            r"saturated|calories|protein|carbohydrate|serving",
            re.I,
        ),
        max_distance=8,
    )

    filtered: List[Dict[str, Any]] = []

    for candidate in candidates:
        raw_value = candidate["raw_text"]
        source_line = candidate.get("source_line", "")

        if re.search(r"(?:/?|per)\s*(?:g|kg|ml|l)\b", raw_value, re.I):
            continue

        numeric_match = re.search(r"\d+(?:[.,]\d+)?", raw_value)
        if numeric_match:
            numeric_value = float(numeric_match.group(0).replace(",", "."))

            if numeric_value < 5 and not re.search(
                r"₹|rs\s*\.|inr",
                raw_value,
                re.I,
            ):
                continue

            if re.search(
                r"serves|serving|per\s+(?:100g|packet|pack|unit)|expiry|use\s+by|best\s+before|batch\s+no",
                source_line,
                re.I,
            ) or DATE.search(source_line):
                continue

        filtered.append(candidate)

    if filtered:
        contextual_prices = [
            candidate
            for candidate in filtered
            if re.search(
                r"₹|rs\s*\.?|inr|usp",
                f"{candidate.get('raw_text', '')} {candidate.get('source_line', '')}",
                re.I,
            )
        ]

        if contextual_prices:
            filtered = contextual_prices

        def mrp_candidate_score(candidate: Dict[str, Any]) -> float:
            base_score = candidate.get("confidence", 0.0) + max(
                0,
                3 - candidate.get("distance", 3),
            ) * 0.2

            raw_text = candidate.get("raw_text", "")
            if re.search(r"₹|rs\s*\.|inr", raw_text, re.I):
                base_score += 0.3

            if (
                "(" in candidate.get("source_line", "")
                and ")" in candidate.get("source_line", "")
            ):
                base_score += 0.2

            return base_score

        selected = max(filtered, key=mrp_candidate_score)
        normalized = _normalize_mrp_value(selected["value"])

        if normalized:
            logger.info("MRP_EXTRACT method=fallback value=%s", normalized)
            logger.info(
                "MRP_SOURCE method=%s value=%r raw_has_mrp=%s",
                "fallback",
                normalized,
                bool(
                    re.search(
                        r"\bM\s*\.?\s*R\s*\.?\s*P\b|maximum\s+retail",
                        raw_full_text,
                        re.I,
                    )
                ),
            )

        return normalized

    logger.info("MRP_EXTRACT method=not_found")
    logger.info(
        "MRP_SOURCE method=%s value=%r raw_has_mrp=%s",
        "not_found",
        None,
        bool(
            re.search(
                r"\bM\s*\.?\s*R\s*\.?\s*P\b|maximum\s+retail",
                raw_full_text,
                re.I,
            )
        ),
    )
    return None


def _extract_net_quantity(
    lines: List[Dict[str, Any]],
    raw_full_text: str = "",
) -> str | None:
    if raw_full_text:
        net_patterns = [
            r"\bNET\s*(?:WT\.?|WEIGHT|QUANTITY|QTY|CONTENTS?)\s*[:\-]?\s*(\d{1,5}(?:[.,]\d+)?)\s*(mg|kg|g|ml|l)\b",
            r"\b(\d{1,5}(?:[.,]\d+)?)\s*(mg|kg|g|ml|l)\s*NET\b",
            r"\bNET\s*(\d{1,5}(?:[.,]\d+)?)\s*(mg|kg|g|ml|l)\b",
        ]

        for pattern in net_patterns:
            match = re.search(pattern, raw_full_text, re.I)
            if not match:
                continue

            quantity_str = match.group(1)
            unit = match.group(2).lower()
            context = raw_full_text[match.start() : match.end() + 20]

            if re.search(
                r"nutrition|serving|per\s+100g|calories|fat|saturated|protein|rda",
                context,
                re.I,
            ):
                continue

            normalized = _normalize_quantity_value(f"{quantity_str} {unit}")
            if normalized:
                logger.info(
                    "NET_QTY_EXTRACT method=explicit_label value=%s confidence=high",
                    normalized,
                )
                return normalized

    candidates = value_following_label(
        lines,
        LABELS["NET_QUANTITY"],
        QUANTITY,
        re.compile(
            r"nutrition|saturated|serving|calories|protein|carbohydrate",
            re.I,
        ),
        max_distance=8,
    )

    selected = _choose_candidate(candidates)
    if selected:
        normalized = _normalize_quantity_value(selected["value"])
        if normalized:
            logger.info(
                "NET_QTY_EXTRACT method=fallback value=%s confidence=medium",
                normalized,
            )
        return normalized

    logger.info("NET_QTY_EXTRACT method=not_found")
    return None


def _extract_mfg_date(
    lines: List[Dict[str, Any]],
    raw_full_text: str = "",
) -> str | None:
    """
    Extract manufacture/packing date.

    Supports:
    - DATE OF MANUFACTURE: 24/06/2026
    - OCR-attached extra year digit: 24/06/20265 -> 24/06/2026
    - MFD & USE BY: 13/07/26 & 10/12/2026
      where the first date is always manufacture date.
    """
    raw_text = raw_full_text or "\n".join(
        line.get("raw_line_text", line["text"])
        for line in lines
    )

    combined_pattern = re.compile(
        r"(?:\bMFD\b|\bMFG\b|manufactured?)"
        r"\s*(?:&|/|and)\s*"
        r"(?:use\s*by|expiry|exp\.?|best\s*before)"
        r"\s*[:#.\-]?\s*"
        r"(?P<context>.{0,100})",
        re.I | re.S,
    )

    for match in combined_pattern.finditer(raw_text):
        date_values = _find_date_strings(match.group("context"))
        if not date_values:
            continue

        normalized, repaired = _normalize_mfg_date_value(date_values[0])
        if normalized:
            logger.info(
                "MFG_DATE_EXTRACT method=combined_label value=%s",
                normalized,
            )
            if repaired:
                logger.info(
                    "MFG_DATE_EXTRACT method=ocr_repair raw=%s normalized=%s",
                    date_values[0],
                    normalized,
                )
            return normalized

    explicit_pattern = re.compile(
        r"(?:"
        r"date\s+of\s+(?:mfg|manufacture|packing)"
        r"|mfg"
        r"|mfd"
        r"|manufacture"
        r"|manufactured"
        r"|pkd"
        r"|packed\s+on"
        r")"
        r"\s*[:#.\-]?\s*"
        r"(?P<context>.{0,100})",
        re.I | re.S,
    )

    for match in explicit_pattern.finditer(raw_text):
        context = match.group("context")

        first_expiry = re.search(
            r"\b(?:use\s+by|expiry|exp\.?|best\s+before)\b",
            context,
            re.I,
        )

        manufacture_context = (
            context[: first_expiry.start()]
            if first_expiry
            else context
        )

        date_values = _find_date_strings(manufacture_context)
        if not date_values:
            continue

        normalized, repaired = _normalize_mfg_date_value(date_values[0])
        if normalized:
            if repaired:
                logger.info(
                    "MFG_DATE_EXTRACT method=ocr_repair raw=%s normalized=%s",
                    date_values[0],
                    normalized,
                )
            else:
                logger.info(
                    "MFG_DATE_EXTRACT method=explicit_label value=%s",
                    normalized,
                )
            return normalized

    candidates = value_following_label(
        lines,
        LABELS["MFG_DATE"],
        DATE,
        None,
        max_distance=6,
    )

    for candidate in candidates:
        source_line = candidate.get("source_line", "")
        if LABELS["EXPIRY"].search(source_line):
            continue

        normalized, repaired = _normalize_mfg_date_value(candidate["raw_text"])
        if normalized:
            if repaired:
                logger.info(
                    "MFG_DATE_EXTRACT method=ocr_repair raw=%s normalized=%s",
                    candidate["raw_text"],
                    normalized,
                )
            else:
                logger.info(
                    "MFG_DATE_EXTRACT method=fallback value=%s",
                    normalized,
                )
            return normalized

    logger.info("MFG_DATE_EXTRACT method=not_found")
    return None


def _is_valid_mfg_date(value: str | None) -> bool:
    if not value:
        return False

    normalized, _ = _normalize_mfg_date_value(value)
    return normalized is not None


def _valid_mfg_candidates(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = value_after_label(lines, LABELS["MFG_DATE"], DATE)
    valid_candidates: List[Dict[str, Any]] = []

    for candidate in candidates:
        normalized, _ = _normalize_mfg_date_value(candidate.get("raw_text", ""))
        if normalized:
            valid_candidates.append(candidate)

    return valid_candidates


def _extract_contact(lines: List[Dict[str, Any]]) -> str | None:
    candidates = []

    for i, line in enumerate(lines):
        if LABELS["CONSUMER_CARE"].search(line["text"]):
            text = " ".join(
                item["text"] for _, item in nearby_lines(lines, i, 2)
            )
            if PHONE.search(text) or EMAIL.search(text) or len(text) >= 12:
                candidates.append(
                    {
                        "value": text,
                        "confidence": line.get("confidence", 0.0),
                        "distance": 0,
                    }
                )

    return choose_highest_confidence_candidate(candidates)


def _extract_manufacturer(lines: List[Dict[str, Any]]) -> str | None:
    candidates = []

    for i, line in enumerate(lines):
        if LABELS["MANUFACTURER_NAME"].search(line["text"]):
            text = " ".join(
                item["text"] for _, item in nearby_lines(lines, i, 2)
            )

            has_name = len(re.findall(r"[A-Za-z]{3,}", text)) >= 2
            has_location = bool(
                re.search(
                    r"address|road|plot|mumbai|delhi|bangalore|maharashtra|india|pin\s*\d",
                    text,
                    re.I,
                )
            )

            if has_name and has_location:
                candidates.append(
                    {
                        "value": text,
                        "confidence": line.get("confidence", 0.0),
                        "distance": 0,
                    }
                )

    return choose_highest_confidence_candidate(candidates)


def _extract_common_name(lines: List[Dict[str, Any]]) -> str | None:
    candidates = [
        {
            "value": line["text"],
            "confidence": line.get("confidence", 0.0),
            "distance": i,
            "raw_text": line.get("raw_line_text", line["text"]),
            "source_line": line.get("raw_line_text", line["text"]),
        }
        for i, line in enumerate(lines[:8])
        if LABELS["COMMON_NAME"].search(line["text"])
        and not re.search(r"fried in|nutrition|ingredients", line["text"], re.I)
    ]

    return choose_highest_confidence_candidate(candidates)


def run_compliance_check(
    ocr: str | Dict[str, Any] | Iterable[Dict[str, Any]]
) -> Tuple[List[Dict], List[Dict]]:
    lines = _ordered_lines(ocr)

    raw_full_text = ""
    if isinstance(ocr, dict):
        raw_full_text = str(ocr.get("full_text") or "")
    elif isinstance(ocr, str):
        raw_full_text = ocr

    logger.debug("Normalized ordered OCR lines: %s", lines)

    mrp_value = _extract_mrp(lines, raw_full_text)
    net_qty_value = _extract_net_quantity(lines, raw_full_text)
    mfg_value = _extract_mfg_date(lines, raw_full_text)

    mrp_candidates = value_following_label(
        lines,
        LABELS["MRP"],
        MONEY,
        re.compile(
            r"/\s*g|saturated|calories|protein|carbohydrate|serving|cashback|discount|free",
            re.I,
        ),
        max_distance=5,
    )

    net_qty_candidates = value_following_label(
        lines,
        LABELS["NET_QUANTITY"],
        QUANTITY,
        re.compile(
            r"nutrition|saturated|serving|calories|protein|carbohydrate",
            re.I,
        ),
        max_distance=5,
    )

    candidate_lists = {
        "MRP": mrp_candidates,
        "NET_QUANTITY": net_qty_candidates,
        "MFG_DATE": [],
        "COUNTRY_OF_ORIGIN": value_after_label(
            lines,
            re.compile(
                r"\b(?:country\s+of\s+origin|made\s+in|product\s+of|imported\s+from)\b",
                re.I,
            ),
            re.compile(r"[A-Za-z][A-Za-z .&-]{2,40}"),
        ),
    }

    selected = {
        field: _choose_candidate(candidates)
        for field, candidates in candidate_lists.items()
    }

    if mrp_value is not None:
        mrp_number = re.search(r"\d+(?:[.,]\d+)?", mrp_value)
        source = next(
            (
                line
                for line in lines
                if mrp_number
                and mrp_number.group(0).replace(",", ".")
                in line["text"].replace(",", ".")
            ),
            None,
        )

        selected["MRP"] = {
            "value": mrp_value,
            "raw_text": mrp_value,
            "source_line": (
                source.get("raw_line_text", source["text"])
                if source
                else mrp_value
            ),
            "confidence": 1.0,
            "distance": 0,
            "line": source.get("line_number", 0) if source else 0,
        }

    if net_qty_value is not None:
        selected["NET_QUANTITY"] = {
            "value": net_qty_value,
            "raw_text": net_qty_value,
            "source_line": net_qty_value,
            "confidence": 1.0,
            "distance": 0,
            "line": 0,
        }

    if mfg_value is not None:
        selected["MFG_DATE"] = {
            "value": mfg_value,
            "raw_text": mfg_value,
            "source_line": mfg_value,
            "confidence": 1.0,
            "distance": 0,
            "line": 0,
        }
    else:
        selected["MFG_DATE"] = None

    if selected.get("MRP") and re.search(
        r"expiry|use\s+by|best\s+before|batch\s+no",
        selected["MRP"].get("source_line", ""),
        re.I,
    ):
        selected["MRP"] = None

    manufacturer = _extract_manufacturer(lines)
    contact = _extract_contact(lines)
    common_name = _extract_common_name(lines)

    selected["MANUFACTURER_NAME"] = (
        {
            "value": manufacturer,
            "confidence": 0.0,
            "distance": 0,
            "raw_text": manufacturer,
            "source_line": "",
        }
        if manufacturer
        else None
    )

    selected["CONSUMER_CARE"] = (
        {
            "value": contact,
            "confidence": 0.0,
            "distance": 0,
            "raw_text": contact,
            "source_line": "",
        }
        if contact
        else None
    )

    selected["COMMON_NAME"] = (
        {
            "value": common_name,
            "confidence": 0.0,
            "distance": 0,
            "raw_text": common_name,
            "source_line": "",
        }
        if common_name
        else None
    )

    if selected["MRP"]:
        raw_text = selected["MRP"].get("raw_text", "")
        numeric_match = re.search(r"\d+(?:[.,]\d+)?", raw_text)

        if numeric_match:
            numeric_value = float(numeric_match.group(0).replace(",", "."))
            if numeric_value < 1 or re.search(r"/\s*g", raw_text, re.I):
                selected["MRP"] = None

    values = {
        field: candidate["value"] if candidate else None
        for field, candidate in selected.items()
    }

    if mrp_value is not None:
        values["MRP"] = mrp_value
    elif selected["MRP"]:
        values["MRP"] = _normalize_mrp_value(selected["MRP"]["value"])

    if net_qty_value is not None:
        values["NET_QUANTITY"] = net_qty_value
    elif selected["NET_QUANTITY"]:
        values["NET_QUANTITY"] = _normalize_quantity_value(
            selected["NET_QUANTITY"]["value"]
        )

    if mfg_value is not None:
        values["MFG_DATE"] = mfg_value

    logger.info(
        "MRP DEBUG raw_full_text_has_49=%s selected_mrp=%r",
        "49.00" in raw_full_text,
        values.get("MRP"),
    )

    fields: List[Dict] = []
    violations: List[Dict] = []

    for field_name, value in values.items():
        candidate = selected.get(field_name)

        label_found = (
            any(
                LABELS.get(field_name, re.compile(r"$^")).search(line["text"])
                for line in lines
            )
            if field_name in LABELS
            else False
        )

        label_confidence = max(
            (
                float(line.get("confidence", 0.0))
                for line in lines
                if field_name in LABELS
                and LABELS[field_name].search(line["text"])
            ),
            default=0.0,
        )

        confidence = (
            float(candidate.get("confidence", 0.0))
            if candidate
            else label_confidence
        )

        numeric_value = re.search(r"\d+(?:[.,]\d+)?", value or "")
        suspicious_mrp = (
            field_name == "MRP"
            and numeric_value is not None
            and float(numeric_value.group(0).replace(",", ".")) < 1
        )

        if (
            field_name == "MFG_DATE"
            and value not in (None, "", [])
            and not _is_valid_mfg_date(value)
        ):
            state = "needs_review"
        elif value not in (None, "", []) and not suspicious_mrp:
            state = "verified_present"
        elif field_name == "MFG_DATE" and candidate and candidate.get("raw_text"):
            state = "needs_review"
        elif (
            field_name in ("COUNTRY_OF_ORIGIN", "CONSUMER_CARE")
            and value is None
            and not label_found
        ):
            state = "not_applicable"
        else:
            state = (
                "verified_missing"
                if label_found and confidence >= 0.65
                else "not_detected_needs_review"
            )

        if field_name == "COUNTRY_OF_ORIGIN" and not re.search(
            r"import|imported|foreign|made\s+in",
            " ".join(line["text"] for line in lines),
            re.I,
        ):
            if state != "verified_present":
                state = "not_applicable"

        candidate_line = candidate.get("line") if candidate else None
        source_line = (
            lines[candidate_line]["text"]
            if isinstance(candidate_line, int) and candidate_line < len(lines)
            else None
        )

        candidate_status = None

        if (
            field_name == "MRP"
            and value is not None
            and (suspicious_mrp or confidence < 0.65)
        ):
            candidate_status = "low_confidence_candidate"

        fields.append(
            {
                "field_name": field_name,
                "field_value": value,
                "is_present": state == "verified_present",
                "verification_state": state,
                "candidate_status": candidate_status,
                "raw_text": candidate.get("raw_text") if candidate else None,
                "source_line": (
                    candidate.get("source_line") if candidate else source_line
                ),
                "confidence": confidence,
            }
        )

        if (
            state == "verified_missing"
            and field_name
            not in {
                "NET_QUANTITY",
                "COMMON_NAME",
                "MFG_DATE",
                "COUNTRY_OF_ORIGIN",
                "CONSUMER_CARE",
            }
        ):
            violations.append(
                {
                    "rule_code": RULE_METADATA[field_name]["rule_code"],
                    "description": RULE_METADATA[field_name]["description"],
                }
            )

    logger.debug("Final extracted fields: %s", fields)
    return fields, violations