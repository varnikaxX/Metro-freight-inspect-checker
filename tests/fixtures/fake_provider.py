"""Test doubles for the OCR provider interface.

No network access or Google credentials are required to use these.
"""
from __future__ import annotations

from app.models.ocr_document import BoundingBox, BoundingBoxVertex, OCRDocument, OCRLine
from app.providers.base import OCRProvider, OCRProviderProcessingError, OCRProviderUnavailableError


def make_line(text: str) -> OCRLine:
    box = BoundingBox(vertices=[BoundingBoxVertex(x=0, y=0), BoundingBoxVertex(x=10, y=10)])
    return OCRLine(text=text, bounding_box=box, provider_confidence=0.95, words=[])


def document_from_lines(lines: list[str]) -> OCRDocument:
    ocr_lines = [make_line(line) for line in lines]
    full_text = "\n".join(lines)
    return OCRDocument(full_text=full_text, lines=ocr_lines, provider_name="fake")


class FakeOCRProvider(OCRProvider):
    """A fake provider that returns pre-programmed OCRDocuments per call.

    Queue documents with `queue_document`/`queue_lines`, or configure a
    single error with `queue_error` for failure-path tests.
    """

    def __init__(self) -> None:
        self._queue: list[OCRDocument] = []
        self._raise: Exception | None = None

    def queue_document(self, document: OCRDocument) -> None:
        self._queue.append(document)

    def queue_lines(self, lines: list[str]) -> None:
        self._queue.append(document_from_lines(lines))

    def queue_error(self, exc: Exception) -> None:
        self._raise = exc

    def detect_text(self, image_bytes: bytes) -> OCRDocument:
        if self._raise is not None:
            exc, self._raise = self._raise, None
            raise exc
        if not self._queue:
            return OCRDocument(full_text="", lines=[], provider_name="fake")
        return self._queue.pop(0)


__all__ = [
    "FakeOCRProvider",
    "document_from_lines",
    "make_line",
    "OCRProviderProcessingError",
    "OCRProviderUnavailableError",
]
