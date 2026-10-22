"""Image preparation helpers for photographed package labels."""

from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger("image_preprocessor")


def _decode_image(image_bytes: bytes) -> np.ndarray:
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    encoded = io.BytesIO()
    image.save(encoded, format="PNG")
    decoded = cv2.imdecode(np.frombuffer(encoded.getvalue(), np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise ValueError("Uploaded bytes are not a readable image.")
    return decoded


def _resize_for_small_text(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    longest_side = max(height, width)
    if longest_side < 1800:
        scale = 1800 / longest_side
        image = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_CUBIC)
    return image


def preprocess_variants(image_bytes: bytes, debug: bool = False) -> list[bytes]:
    """Return original-enhanced, adaptive-threshold, and Otsu JPEG variants."""
    color = _resize_for_small_text(_decode_image(image_bytes))
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)

    # CLAHE recovers lettering lost in uneven packet lighting and glare.
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 7, 7, 21)

    adaptive = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    variants: list[tuple[str, np.ndarray]] = [
        ("enhanced", denoised),
        ("adaptive", adaptive),
        ("otsu", otsu),
    ]
    encoded_variants: list[bytes] = []
    for name, variant in variants:
        ok, encoded = cv2.imencode(".jpg", variant, [cv2.IMWRITE_JPEG_QUALITY, 94])
        if not ok:
            raise ValueError(f"Could not encode {name} OCR variant.")
        data = encoded.tobytes()
        encoded_variants.append(data)
        if debug and name == "enhanced":
            debug_path = Path(tempfile.gettempdir()) / "debug_preprocessed.jpg"
            debug_path.write_bytes(data)
            logger.info("Saved preprocessed OCR image to %s", debug_path)

    return encoded_variants


def _pil_variants(image_bytes: bytes, debug: bool = False) -> list[bytes]:
    """Small dependency-free fallback used if OpenCV is not installed yet."""
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("L")
    image = ImageOps.autocontrast(image)
    if max(image.size) < 1800:
        scale = 1800 / max(image.size)
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    threshold = image.point(lambda value: 255 if value > 165 else 0)
    variants = [image, threshold]
    encoded_variants = []
    for index, variant in enumerate(variants):
        output = io.BytesIO()
        variant.save(output, format="JPEG", quality=94)
        data = output.getvalue()
        encoded_variants.append(data)
        if debug and index == 0:
            debug_path = Path(tempfile.gettempdir()) / "debug_preprocessed.jpg"
            debug_path.write_bytes(data)
            logger.info("Saved fallback OCR image to %s", debug_path)
    return encoded_variants


def preprocess_for_ocr(image_bytes: bytes) -> bytes:
    """Return the primary enhanced image variant for callers needing one image."""
    return preprocess_variants(image_bytes, debug=os.getenv("DEBUG_OCR", "false").lower() == "true")[0]
