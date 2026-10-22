"""
services/ocr.py
----------------
Local Tesseract OCR integration for extracting text from packaged-commodity
label images. Swapped in from Google Cloud Vision to avoid requiring a
billing-enabled GCP project during hackathon development.

Requires:
  - The Tesseract binary installed on the machine (not just the pip package):
      Windows: https://github.com/UB-Mannheim/tesseract/wiki  (installer)
      macOS:   brew install tesseract
      Linux:   sudo apt install tesseract-ocr
  - `pip install pytesseract pillow`

If Tesseract isn't on PATH, set TESSERACT_CMD in .env to the full path of
tesseract.exe (Windows default is usually
C:\\Program Files\\Tesseract-OCR\\tesseract.exe).
"""

import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytesseract
from PIL import Image

from config import settings
from services.image_preprocessor import preprocess_variants
from services.google_vision_ocr import document_ocr

logger = logging.getLogger(__name__)
logger = logging.getLogger("ocr_service")

# Allow overriding the Tesseract binary path via environment variable.  If
# Tesseract is installed elsewhere, adjust TESSERACT_CMD in ``backend/.env``.
DEFAULT_WINDOWS_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_tesseract_cmd = (
    getattr(settings, "TESSERACT_CMD", None)
    or os.environ.get("TESSERACT_CMD")
    or DEFAULT_WINDOWS_TESSERACT_CMD
)
pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


def _ensure_tesseract_available() -> None:
    """Raise a clear setup error when the configured Tesseract executable is absent."""
    executable = Path(pytesseract.pytesseract.tesseract_cmd)
    if not executable.is_file():
        raise RuntimeError(
            "Tesseract OCR executable was not found at "
            f"'{executable}'. Install the UB Mannheim Windows build from "
            "https://github.com/UB-Mannheim/tesseract/wiki, then set "
            "TESSERACT_CMD in backend/.env if your installation uses a "
            "different path."
        )


def _run_tesseract(image_bytes: bytes) -> Dict[str, Any]:
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    config = "--psm 6"
    language = getattr(settings, "OCR_LANGUAGE", "eng")
    full_text = pytesseract.image_to_string(image, lang=language, config=config)
    data = pytesseract.image_to_data(
        image, lang=language, output_type=pytesseract.Output.DICT, config=config
    )

    blocks_map: Dict[int, Dict[str, Any]] = {}
    for i, raw_word in enumerate(data["text"]):
        word = raw_word.strip()
        if not word:
            continue
        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError):
            confidence = -1.0
        x, y, width, height = (data[key][i] for key in ("left", "top", "width", "height"))
        block_num = data["block_num"][i]
        entry = blocks_map.setdefault(
            block_num,
            {"words": [], "confidences": [], "min_x": x, "min_y": y, "max_x": x + width, "max_y": y + height},
        )
        entry["words"].append(word)
        if confidence >= 0:
            entry["confidences"].append(confidence)
        entry["min_x"] = min(entry["min_x"], x)
        entry["min_y"] = min(entry["min_y"], y)
        entry["max_x"] = max(entry["max_x"], x + width)
        entry["max_y"] = max(entry["max_y"], y + height)

    blocks = []
    for entry in blocks_map.values():
        confidences = entry["confidences"]
        blocks.append(
            {
                "text": " ".join(entry["words"]),
                "confidence": round(sum(confidences) / len(confidences) / 100, 4) if confidences else 0.0,
                "bounding_box": [
                    {"x": entry["min_x"], "y": entry["min_y"]},
                    {"x": entry["max_x"], "y": entry["min_y"]},
                    {"x": entry["max_x"], "y": entry["max_y"]},
                    {"x": entry["min_x"], "y": entry["max_y"]},
                ],
            }
        )
    average_confidence = sum(block["confidence"] for block in blocks) / len(blocks) if blocks else 0.0
    return {"full_text": full_text, "blocks": blocks, "confidence": average_confidence}


def _merge_text(*texts: str) -> str:
    """Keep useful lines from multiple engines without tripling duplicates."""
    merged: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for line in text.splitlines():
            cleaned = " ".join(line.split()).strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                merged.append(cleaned)
    return "\n".join(merged)


def _convert_google_vision_to_dict(google_result) -> Dict[str, Any]:
    """Convert Google Vision OcrResult to the standard OCR dict format."""
    blocks = []
    for line in google_result.lines:
        blocks.append({
            "text": line.text,
            "confidence": line.confidence,
            "bounding_box": [{"x": x, "y": y} for x, y in line.bounding_box],
        })
    return {
        "success": True,
        "full_text": google_result.full_text,
        "blocks": blocks,
        "error": None,
    }


def extract_text_from_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Run OCR on raw image bytes using Google Cloud Vision (primary) or Tesseract (fallback).

    If OCR_ENGINE is set to "tesseract", uses local Tesseract only.
    Otherwise, attempts Google Cloud Vision first, then falls back to Tesseract on error.

    Returns the same shape the rest of the app expects:
    {
        "success": bool,
        "full_text": str,
        "blocks": [
            {
                "text": str,
                "confidence": float,
                "bounding_box": [{"x": int, "y": int}, ...]
            },
            ...
        ],
        "error": str | None
    }

    On any failure this does NOT raise -- it returns success=False so the
    calling route can persist a scan record with status=FAILED.
    """
    if not image_bytes:
        return {
            "success": False,
            "full_text": "",
            "blocks": [],
            "error": "Empty image payload received.",
        }

    ocr_engine = getattr(settings, "OCR_ENGINE", "google_vision").lower()
    debug = bool(getattr(settings, "DEBUG_OCR", False))

    # --- Tesseract-only mode ---
    if ocr_engine == "tesseract":
        return _extract_with_tesseract_only(image_bytes, debug)

    # --- Google Vision primary, Tesseract fallback ---
    # Try Google Vision first
    google_result = _try_google_vision(image_bytes, debug)
    if google_result is not None:
        return google_result

    # Fall back to Tesseract if Google Vision failed/errored/returned empty text
    logger.info("Google Vision OCR failed or returned empty text; falling back to Tesseract")
    return _extract_with_tesseract_only(image_bytes, debug)


def _try_google_vision(image_bytes: bytes, debug: bool) -> Dict[str, Any] | None:
    """Attempt Google Cloud Vision OCR. Return None on error or empty result."""
    try:
        # Write image bytes to temp file since document_ocr expects a file path
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(image_bytes)

        try:
            result = document_ocr(tmp_path)
            
            if debug:
                logger.info("Google Vision OCR succeeded; full_text length: %d chars", len(result.full_text))
            
            # Return None if Google Vision returned empty text (triggers Tesseract fallback)
            if not result.full_text.strip():
                logger.warning("Google Vision OCR returned empty text")
                return None
            
            # Success: convert to standard format
            dict_result = _convert_google_vision_to_dict(result)
            if debug:
                logger.info("Google Vision result: full_text=%r", result.full_text[:100])
            return dict_result

        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except Exception:  # noqa: BLE001
                pass

    except Exception as exc:  # noqa: BLE001 - broad fallback by design
        logger.warning("Google Vision OCR failed: %s", type(exc).__name__)
        if debug:
            logger.debug("Google Vision OCR error details: %s", str(exc)[:200])
        return None


def _extract_with_tesseract_only(image_bytes: bytes, debug: bool) -> Dict[str, Any]:
    """Run Tesseract OCR with preprocessing variants."""
    try:
        variants = preprocess_variants(image_bytes, debug=debug)
        tesseract_results: list[Dict[str, Any]] = []
        for index, variant in enumerate(variants):
            result = _run_tesseract(variant)
            tesseract_results.append(result)
            if debug:
                logger.info("Tesseract variant %d raw OCR: %r", index + 1, result["full_text"])

        best_tesseract = max(
            tesseract_results,
            key=lambda result: (result["confidence"], len(result["full_text"].strip())),
            default={"full_text": "", "blocks": [], "confidence": 0.0},
        )
        full_text = _merge_text(*(result["full_text"] for result in tesseract_results))
        blocks = best_tesseract["blocks"]

        if debug:
            logger.info("Best Tesseract OCR confidence: %.3f", best_tesseract["confidence"])

        if not full_text.strip():
            return {
                "success": True,
                "full_text": "",
                "blocks": [],
                "error": None,
            }

        return {
            "success": True,
            "full_text": full_text,
            "blocks": blocks,
            "error": None,
        }

    except (pytesseract.TesseractNotFoundError, RuntimeError) as exc:
        logger.error("Tesseract binary not found: %s", exc)
        return {
            "success": False,
            "full_text": "",
            "blocks": [],
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001 - broad fallback by design
        logger.exception("Unexpected error during Tesseract OCR processing")
        return {
            "success": False,
            "full_text": "",
            "blocks": [],
            "error": f"Unexpected OCR error: {exc}",
        }
