"""OCR scan orchestrator.

Coordinates the per-image pipeline (download -> validate -> OCR ->
extraction) and multi-image aggregation into the final scan response.

Processing is intentionally SEQUENTIAL: Google Vision SDK calls are
blocking, so no asyncio concurrency is used around them. `process_image`
is kept isolated so that future concurrency (e.g. a thread pool) can be
introduced without restructuring the orchestrator.
"""
from __future__ import annotations

import logging

from app.extractors.dates import DateExtractor
from app.extractors.manufacturer import ManufacturerExtractor
from app.extractors.price import MRPExtractor
from app.extractors.quantity import QuantityExtractor
from app.models.ocr_document import OCRDocument
from app.models.request import ImageInput, ScanRequest
from app.models.response import (
    ErrorCode,
    ImageResult,
    ImageStatus,
    ScanError,
    ScanResponse,
    ScanStatus,
    ScanSummary,
)
from app.providers.base import OCRProvider, OCRProviderProcessingError, OCRProviderUnavailableError
from app.services.aggregator import Aggregator
from app.services.image_service import (
    ImageDownloadError,
    ImageService,
    ImageTooLargeError,
    InvalidImageError,
)

logger = logging.getLogger(__name__)


class _ImageProcessingOutcome:
    """Internal container for the result of processing a single image."""

    def __init__(
        self,
        image_id: str,
        image_result: ImageResult,
        document: OCRDocument | None,
        error: ScanError | None,
    ) -> None:
        self.image_id = image_id
        self.image_result = image_result
        self.document = document
        self.error = error


class OCROrchestrator:
    """Runs the OCR pipeline for a scan request."""

    def __init__(self, provider: OCRProvider, image_service: ImageService) -> None:
        self._provider = provider
        self._image_service = image_service
        self._aggregator = Aggregator()
        self._mrp_extractor = MRPExtractor()
        self._quantity_extractor = QuantityExtractor()
        self._date_extractor = DateExtractor()
        self._manufacturer_extractor = ManufacturerExtractor()

    def run_scan(self, request: ScanRequest) -> ScanResponse:
        scan_id = request.scan_id
        outcomes: list[_ImageProcessingOutcome] = []

        for image_input in request.images:
            logger.info("scan_id=%s image_id=%s stage=start", scan_id, image_input.image_id)
            outcomes.append(self.process_image(scan_id, image_input))

        return self._build_response(scan_id, request.images, outcomes)

    def process_image(self, scan_id: str, image_input: ImageInput) -> _ImageProcessingOutcome:
        """Process a single image in isolation.

        Kept as a standalone method so a future concurrent implementation
        can call this per image without reworking the orchestrator.
        """
        image_id = image_input.image_id

        try:
            image_bytes = self._image_service.fetch_and_validate(str(image_input.image_url))
        except ImageDownloadError as exc:
            logger.warning(
                "scan_id=%s image_id=%s stage=download status=failed code=%s",
                scan_id, image_id, ErrorCode.IMAGE_DOWNLOAD_FAILED.value,
            )
            return self._failure_outcome(image_id, ErrorCode.IMAGE_DOWNLOAD_FAILED, str(exc))
        except ImageTooLargeError as exc:
            logger.warning(
                "scan_id=%s image_id=%s stage=validate status=failed code=%s",
                scan_id, image_id, ErrorCode.IMAGE_TOO_LARGE.value,
            )
            return self._failure_outcome(image_id, ErrorCode.IMAGE_TOO_LARGE, str(exc))
        except InvalidImageError as exc:
            logger.warning(
                "scan_id=%s image_id=%s stage=validate status=failed code=%s",
                scan_id, image_id, ErrorCode.INVALID_IMAGE.value,
            )
            return self._failure_outcome(image_id, ErrorCode.INVALID_IMAGE, str(exc))

        try:
            document = self._provider.detect_text(image_bytes)
        except OCRProviderUnavailableError as exc:
            logger.error(
                "scan_id=%s image_id=%s stage=ocr status=failed code=%s",
                scan_id, image_id, ErrorCode.OCR_PROVIDER_UNAVAILABLE.value,
            )
            return self._failure_outcome(image_id, ErrorCode.OCR_PROVIDER_UNAVAILABLE, str(exc))
        except OCRProviderProcessingError as exc:
            logger.error(
                "scan_id=%s image_id=%s stage=ocr status=failed code=%s",
                scan_id, image_id, ErrorCode.OCR_PROVIDER_ERROR.value,
            )
            return self._failure_outcome(image_id, ErrorCode.OCR_PROVIDER_ERROR, str(exc))
        except Exception as exc:  # noqa: BLE001 - never let one image crash the scan
            logger.exception(
                "scan_id=%s image_id=%s stage=ocr status=failed code=%s",
                scan_id, image_id, ErrorCode.OCR_PROCESSING_FAILED.value,
            )
            return self._failure_outcome(image_id, ErrorCode.OCR_PROCESSING_FAILED, str(exc))

        logger.info("scan_id=%s image_id=%s stage=ocr status=success", scan_id, image_id)

        image_result = ImageResult(
            image_id=image_id,
            status=ImageStatus.SUCCESS,
            text_detected=document.text_detected,
            raw_text=document.full_text,
            error=None,
        )
        return _ImageProcessingOutcome(image_id=image_id, image_result=image_result, document=document, error=None)

    def _failure_outcome(self, image_id: str, code: ErrorCode, message: str) -> _ImageProcessingOutcome:
        error = ScanError(image_id=image_id, code=code, message=message)
        image_result = ImageResult(
            image_id=image_id,
            status=ImageStatus.FAILED,
            text_detected=False,
            raw_text=None,
            error=error,
        )
        return _ImageProcessingOutcome(image_id=image_id, image_result=image_result, document=None, error=error)

    def _run_extractors_safely(self, document: OCRDocument, image_id: str) -> tuple[list, list, list, list]:
        """Run every extractor, isolating failures so one bad extractor
        never blocks the others."""
        mrp_candidates: list = []
        quantity_candidates: list = []
        date_candidates: list = []
        manufacturer_candidates: list = []

        for extractor, bucket in (
            (self._mrp_extractor, mrp_candidates),
            (self._quantity_extractor, quantity_candidates),
            (self._date_extractor, date_candidates),
            (self._manufacturer_extractor, manufacturer_candidates),
        ):
            try:
                bucket.extend(extractor.extract(document, image_id))
            except Exception:  # noqa: BLE001 - one extractor failing must not stop others
                logger.exception("image_id=%s extractor=%s status=failed", image_id, extractor.field_name)

        return mrp_candidates, quantity_candidates, date_candidates, manufacturer_candidates

    def _build_response(
        self,
        scan_id: str,
        requested_images: list[ImageInput],
        outcomes: list[_ImageProcessingOutcome],
    ) -> ScanResponse:
        image_results = [outcome.image_result for outcome in outcomes]
        errors = [outcome.error for outcome in outcomes if outcome.error is not None]

        all_mrp: list = []
        all_quantity: list = []
        all_dates: list = []
        all_manufacturer: list = []

        images_processed = 0
        for outcome in outcomes:
            if outcome.document is None:
                continue
            images_processed += 1
            mrp, quantity, dates, manufacturer = self._run_extractors_safely(outcome.document, outcome.image_id)
            all_mrp.extend(mrp)
            all_quantity.extend(quantity)
            all_dates.extend(dates)
            all_manufacturer.extend(manufacturer)

        images_received = len(requested_images)
        images_failed = images_received - images_processed

        if images_processed == 0:
            status = ScanStatus.FAILED
        elif images_failed == 0:
            status = ScanStatus.SUCCESS
        else:
            status = ScanStatus.PARTIAL

        fields = self._aggregator.aggregate(all_mrp, all_quantity, all_dates, all_manufacturer)

        summary = ScanSummary(
            images_received=images_received,
            images_processed=images_processed,
            images_failed=images_failed,
        )

        logger.info("scan_id=%s stage=complete status=%s", scan_id, status.value)

        return ScanResponse(
            scan_id=scan_id,
            status=status,
            summary=summary,
            images=image_results,
            fields=fields,
            errors=errors,
        )
