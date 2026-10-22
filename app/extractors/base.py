"""Base extractor interface.

Extractors are independent: one extractor failing must never prevent
others from running. The orchestrator layer is responsible for
isolating extractor failures (see OCROrchestrator._run_extractors_safely).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.ocr_document import OCRDocument


class BaseExtractor(ABC):
    """Common interface implemented by every field extractor."""

    field_name: str

    @abstractmethod
    def extract(self, document: OCRDocument, source_image_id: str) -> list[Any]:
        """Return a list of candidate objects for this field.

        Must never raise for "not found" cases -- return an empty list
        instead. Only truly unexpected internal errors should propagate,
        and even those are caught by the orchestrator so that one
        extractor cannot break the others.
        """
        raise NotImplementedError
