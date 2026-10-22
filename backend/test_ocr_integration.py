"""
Test Google Cloud Vision OCR integration with Tesseract fallback.

All tests use mocks to avoid requiring real GCP credentials or network access.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config import Settings
from services.ocr import (
    extract_text_from_image,
    _try_google_vision,
    _convert_google_vision_to_dict,
)


@pytest.fixture
def fake_image_bytes():
    """Minimal valid JPEG bytes (1x1 pixel)."""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd0\xff\xd9"


@pytest.fixture
def mock_ocr_result():
    """Create a mock Google Vision OcrResult."""
    from services.google_vision_ocr import OcrLine, OcrResult

    return OcrResult(
        full_text="MRP ₹49.00\nNet Qty 500 g",
        lines=[
            OcrLine(
                text="MRP ₹49.00",
                confidence=0.95,
                bounding_box=[(10, 20), (150, 20), (150, 40), (10, 40)],
            ),
            OcrLine(
                text="Net Qty 500 g",
                confidence=0.92,
                bounding_box=[(10, 50), (150, 50), (150, 70), (10, 70)],
            ),
        ],
        engine="google_vision",
        elapsed_ms=250,
    )


class TestConvertGoogleVisionToDict:
    """Test conversion from Google Vision format to internal dict format."""

    def test_conversion_preserves_text_and_confidence(self, mock_ocr_result):
        """Ensure the conversion maintains text and confidence data."""
        result = _convert_google_vision_to_dict(mock_ocr_result)

        assert result["success"] is True
        assert result["error"] is None
        assert result["full_text"] == "MRP ₹49.00\nNet Qty 500 g"
        assert len(result["blocks"]) == 2
        assert result["blocks"][0]["text"] == "MRP ₹49.00"
        assert result["blocks"][0]["confidence"] == 0.95
        assert result["blocks"][1]["text"] == "Net Qty 500 g"
        assert result["blocks"][1]["confidence"] == 0.92

    def test_bounding_box_conversion(self, mock_ocr_result):
        """Ensure bounding box vertices are converted correctly."""
        result = _convert_google_vision_to_dict(mock_ocr_result)

        bbox = result["blocks"][0]["bounding_box"]
        assert len(bbox) == 4
        assert bbox[0] == {"x": 10, "y": 20}
        assert bbox[1] == {"x": 150, "y": 20}


class TestOCREngineSelection:
    """Test that OCR engine selection respects OCR_ENGINE setting."""

    @patch("services.ocr._extract_with_tesseract_only")
    @patch("services.ocr.settings")
    def test_tesseract_mode_skips_google_vision(
        self, mock_settings, mock_tesseract, fake_image_bytes
    ):
        """When OCR_ENGINE='tesseract', Google Vision should not be called."""
        mock_settings.OCR_ENGINE = "tesseract"
        mock_settings.DEBUG_OCR = False
        mock_tesseract.return_value = {
            "success": True,
            "full_text": "Tesseract text",
            "blocks": [],
            "error": None,
        }

        result = extract_text_from_image(fake_image_bytes)

        assert result["success"] is True
        assert result["full_text"] == "Tesseract text"
        mock_tesseract.assert_called_once()

    @patch("services.ocr.document_ocr")
    @patch("services.ocr.settings")
    def test_google_vision_mode_tries_google_first(
        self, mock_settings, mock_document_ocr, fake_image_bytes, mock_ocr_result
    ):
        """When OCR_ENGINE != 'tesseract', Google Vision should be tried first."""
        mock_settings.OCR_ENGINE = "google_vision"
        mock_settings.DEBUG_OCR = False
        mock_document_ocr.return_value = mock_ocr_result

        result = extract_text_from_image(fake_image_bytes)

        assert result["success"] is True
        assert result["full_text"] == "MRP ₹49.00\nNet Qty 500 g"
        assert len(result["blocks"]) == 2
        mock_document_ocr.assert_called_once()


class TestGoogleVisionFallback:
    """Test that Tesseract fallback works when Google Vision fails."""

    @patch("services.ocr._extract_with_tesseract_only")
    @patch("services.ocr.document_ocr")
    @patch("services.ocr.settings")
    def test_fallback_on_google_vision_error(
        self, mock_settings, mock_document_ocr, mock_tesseract, fake_image_bytes
    ):
        """When Google Vision raises an exception, fall back to Tesseract."""
        mock_settings.OCR_ENGINE = "google_vision"
        mock_settings.DEBUG_OCR = False
        mock_document_ocr.side_effect = RuntimeError("Google Cloud Vision failed")
        mock_tesseract.return_value = {
            "success": True,
            "full_text": "Fallback Tesseract text",
            "blocks": [],
            "error": None,
        }

        result = extract_text_from_image(fake_image_bytes)

        assert result["success"] is True
        assert result["full_text"] == "Fallback Tesseract text"
        mock_tesseract.assert_called_once()

    @patch("services.ocr._extract_with_tesseract_only")
    @patch("services.ocr.document_ocr")
    @patch("services.ocr.settings")
    def test_fallback_on_empty_google_vision_result(
        self, mock_settings, mock_document_ocr, mock_tesseract, fake_image_bytes
    ):
        """When Google Vision returns empty text, fall back to Tesseract."""
        from services.google_vision_ocr import OcrLine, OcrResult

        mock_settings.OCR_ENGINE = "google_vision"
        mock_settings.DEBUG_OCR = False
        
        empty_result = OcrResult(
            full_text="",  # Empty!
            lines=[],
            engine="google_vision",
            elapsed_ms=100,
        )
        mock_document_ocr.return_value = empty_result
        mock_tesseract.return_value = {
            "success": True,
            "full_text": "Fallback Tesseract text",
            "blocks": [],
            "error": None,
        }

        result = extract_text_from_image(fake_image_bytes)

        assert result["success"] is True
        assert result["full_text"] == "Fallback Tesseract text"
        mock_tesseract.assert_called_once()


class TestEmptyImageHandling:
    """Test handling of empty or invalid image input."""

    @patch("services.ocr.settings")
    def test_empty_image_bytes_returns_error(self, mock_settings):
        """Empty image bytes should return a proper error response."""
        mock_settings.DEBUG_OCR = False

        result = extract_text_from_image(b"")

        assert result["success"] is False
        assert result["error"] == "Empty image payload received."
        assert result["full_text"] == ""
        assert result["blocks"] == []


class TestComplianceCompatibility:
    """Test that returned format is compatible with compliance.run_compliance_check."""

    @patch("services.ocr.document_ocr")
    @patch("services.ocr.settings")
    def test_google_vision_result_format_compatible_with_compliance(
        self, mock_settings, mock_document_ocr, fake_image_bytes, mock_ocr_result
    ):
        """OCR result must be compatible with compliance.run_compliance_check."""
        from services.compliance import run_compliance_check

        mock_settings.OCR_ENGINE = "google_vision"
        mock_settings.DEBUG_OCR = False
        mock_document_ocr.return_value = mock_ocr_result

        ocr_result = extract_text_from_image(fake_image_bytes)

        # Should not raise; compliance.py accepts dict with blocks or lines
        fields, violations = run_compliance_check(ocr_result)

        assert isinstance(fields, list)
        assert isinstance(violations, list)
        # MRP should be detected
        mrp_field = next((f for f in fields if f["field_name"] == "MRP"), None)
        assert mrp_field is not None
