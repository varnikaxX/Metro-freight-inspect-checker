"""Google Cloud Vision OCR provider implementation.

Converts Google Vision SDK responses into the internal OCRDocument
model. No other part of the application should import
google.cloud.vision directly -- this module is the only boundary.
"""
from __future__ import annotations

import logging

from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.auth.exceptions import GoogleAuthError
from google.cloud import vision

from app.models.ocr_document import BoundingBox, BoundingBoxVertex, OCRDocument, OCRLine, OCRWord
from app.providers.base import OCRProvider, OCRProviderProcessingError, OCRProviderUnavailableError

logger = logging.getLogger(__name__)


def _bounding_box_from_vertices(vertices) -> BoundingBox | None:
    if not vertices:
        return None
    points = [BoundingBoxVertex(x=v.x, y=v.y) for v in vertices]
    return BoundingBox(vertices=points)


def _word_text(word) -> str:
    return "".join(symbol.text for symbol in word.symbols)


def _build_word(word) -> OCRWord:
    return OCRWord(
        text=_word_text(word),
        bounding_box=_bounding_box_from_vertices(word.bounding_box.vertices),
        provider_confidence=getattr(word, "confidence", None) or None,
    )


def _build_line(paragraph) -> OCRLine:
    words = [_build_word(w) for w in paragraph.words]
    text = " ".join(w.text for w in words)
    return OCRLine(
        text=text,
        bounding_box=_bounding_box_from_vertices(paragraph.bounding_box.vertices),
        provider_confidence=getattr(paragraph, "confidence", None) or None,
        words=words,
    )


class GoogleVisionProvider(OCRProvider):
    """OCR provider backed by Google Cloud Vision's document text detection.

    Document text detection (as opposed to plain text detection) is used
    because it is the method recommended by Google for dense/structured
    text such as packaging labels.
    """

    def __init__(self, client: "vision.ImageAnnotatorClient | None" = None) -> None:
        # A client can be injected for testing; otherwise it is created
        # lazily so importing this module never requires credentials.
        self._client = client

    @property
    def client(self) -> "vision.ImageAnnotatorClient":
        if self._client is None:
            try:
                self._client = vision.ImageAnnotatorClient()
            except GoogleAuthError as exc:
                raise OCRProviderUnavailableError("Google Vision credentials are not configured.") from exc
        return self._client

    def detect_text(self, image_bytes: bytes) -> OCRDocument:
        image = vision.Image(content=image_bytes)

        try:
            response = self.client.document_text_detection(image=image)
        except GoogleAuthError as exc:
            raise OCRProviderUnavailableError("Google Vision authentication failed.") from exc
        except RetryError as exc:
            raise OCRProviderUnavailableError("Google Vision is unreachable (retries exhausted).") from exc
        except GoogleAPICallError as exc:
            raise OCRProviderUnavailableError(f"Google Vision API call failed: {exc.message}") from exc
        except Exception as exc:  # noqa: BLE001 - convert any unexpected SDK error
            raise OCRProviderProcessingError(f"Unexpected error calling Google Vision: {exc}") from exc

        if response.error and response.error.message:
            raise OCRProviderProcessingError(f"Google Vision returned an error: {response.error.message}")

        annotation = response.full_text_annotation
        full_text = annotation.text if annotation and annotation.text else ""

        lines: list[OCRLine] = []
        if annotation:
            for page in annotation.pages:
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        lines.append(_build_line(paragraph))

        return OCRDocument(
            full_text=full_text,
            lines=lines,
            provider_name="google_vision",
            provider_metadata={},
        )
