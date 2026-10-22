"""API-level integration tests using FastAPI's TestClient.

No real Google credentials or network access are used: the OCR
provider and image service dependencies are overridden with fakes.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.dependencies import get_image_service, get_ocr_provider
from app.main import app
from app.services.image_service import ImageDownloadError
from tests.fixtures.fake_image_service import FakeImageService
from tests.fixtures.fake_provider import FakeOCRProvider, document_from_lines


def _client_with(provider: FakeOCRProvider, image_service: FakeImageService) -> TestClient:
    app.dependency_overrides[get_ocr_provider] = lambda: provider
    app.dependency_overrides[get_image_service] = lambda: image_service
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_success_single_image():
    provider = FakeOCRProvider()
    provider.queue_document(document_from_lines(["MRP ₹50", "Net Wt. 500g"]))
    client = _client_with(provider, FakeImageService())

    response = client.post(
        "/ocr/scan",
        json={
            "scan_id": "scan_001",
            "images": [{"image_id": "front", "image_url": "https://example.com/front.jpg"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["fields"]["mrp"]["status"] == "found"
    assert body["fields"]["net_quantity"]["status"] == "found"


def test_scan_no_text_detected_is_not_a_failure():
    provider = FakeOCRProvider()
    provider.queue_document(document_from_lines([]))
    client = _client_with(provider, FakeImageService())

    response = client.post(
        "/ocr/scan",
        json={
            "scan_id": "scan_002",
            "images": [{"image_id": "front", "image_url": "https://example.com/front.jpg"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["images"][0]["text_detected"] is False


def test_scan_partial_failure_when_one_image_fails():
    provider = FakeOCRProvider()
    provider.queue_document(document_from_lines(["MRP ₹50"]))
    image_service = FakeImageService()
    image_service.fail_for("https://example.com/back.jpg", ImageDownloadError("boom"))
    client = _client_with(provider, image_service)

    response = client.post(
        "/ocr/scan",
        json={
            "scan_id": "scan_003",
            "images": [
                {"image_id": "front", "image_url": "https://example.com/front.jpg"},
                {"image_id": "back", "image_url": "https://example.com/back.jpg"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["summary"]["images_processed"] == 1
    assert body["summary"]["images_failed"] == 1


def test_scan_total_failure_when_all_images_fail():
    provider = FakeOCRProvider()
    image_service = FakeImageService()
    image_service.fail_for("https://example.com/front.jpg", ImageDownloadError("boom"))
    client = _client_with(provider, image_service)

    response = client.post(
        "/ocr/scan",
        json={
            "scan_id": "scan_004",
            "images": [{"image_id": "front", "image_url": "https://example.com/front.jpg"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"


def test_scan_rejects_too_many_images():
    provider = FakeOCRProvider()
    client = _client_with(provider, FakeImageService())

    images = [
        {"image_id": f"img{i}", "image_url": f"https://example.com/{i}.jpg"} for i in range(10)
    ]
    response = client.post("/ocr/scan", json={"scan_id": "scan_005", "images": images})

    assert response.status_code == 422


def test_multi_image_aggregation_combines_fields_from_both_images():
    provider = FakeOCRProvider()
    provider.queue_document(document_from_lines(["MRP ₹50"]))
    provider.queue_document(document_from_lines(["Net Wt. 500g"]))
    client = _client_with(provider, FakeImageService())

    response = client.post(
        "/ocr/scan",
        json={
            "scan_id": "scan_006",
            "images": [
                {"image_id": "front", "image_url": "https://example.com/front.jpg"},
                {"image_id": "back", "image_url": "https://example.com/back.jpg"},
            ],
        },
    )

    body = response.json()
    assert body["fields"]["mrp"]["status"] == "found"
    assert body["fields"]["net_quantity"]["status"] == "found"
