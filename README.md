# SIH26 Metro Freight Inspect

## OCR Service — Legal Metrology Packaged Commodities Compliance System

This service is the **OCR module** of the Legal Metrology Packaged Commodities
Compliance System, built for Smart India Hackathon. Given one or more package
image URLs, it runs OCR, extracts *candidate* declarations (MRP, net
quantity, manufacturing/expiry-style dates, and manufacturer/packer info),
and returns a stable structured JSON response.

**This service does not decide legal compliance.** It extracts information
and evidence; a separate Legal Rule Engine decides whether declarations are
legally sufficient or valid.

## 2. Architecture
 
```
Main Backend
     │  Image URL(s)
     ▼
OCR API (FastAPI)
     │
     ▼
Request Validation
     │
     ▼
Orchestrator  ──────────────────────────────┐
     │  (sequential, per image)              │
     ▼                                       │
Image Download & Validation (httpx + Pillow) │
     │                                       │
     ▼                                       │
OCR Provider Interface                       │
     │                                       │
     ▼                                       │
Google Cloud Vision                          │
     │                                       │
     ▼                                       │
Internal OCRDocument Model                   │
     │                                       │
     ▼                                       │
Field Extractors (MRP / Quantity / Dates / Manufacturer)
     │                                       │
     ▼                                       │
Candidate Results ◄───────────────────────────┘
     │
     ▼
Multi-Image Aggregation (no conflict resolution)
     │
     ▼
Stable JSON Response ──► Main Backend / Rule Engine
```

Processing across images is **sequential** by design (see Limitations). Each
image is processed in an isolated `process_image()` call so that
concurrency can be introduced later without restructuring the pipeline.

## 3. Responsibility Boundaries

**This service DOES:**
- Download & validate package images
- Run OCR via Google Cloud Vision
- Extract MRP, net quantity, date declarations, and manufacturer/packer text
- Preserve raw OCR evidence and bounding boxes
- Return structured, stable JSON

**This service DOES NOT:**
- Decide legal compliance or whether a declaration is legally mandatory
- Implement Legal Metrology rules or determine violations
- Own database tables, store scan history, or talk to Supabase directly
- Manage authentication or users
- Resolve conflicting values between images (both are returned)
- Calculate physical font size in millimetres
- Implement advanced computer vision (deskew, super-resolution, etc.)

## 4. Project Structure

```
ocr_service/
├── app/
│   ├── main.py               # FastAPI app + error handling
│   ├── config.py             # Settings (env vars)
│   ├── api/routes.py         # /health, /ocr/scan
│   ├── models/
│   │   ├── request.py        # ScanRequest, ImageInput
│   │   ├── response.py       # ScanResponse + field/candidate models
│   │   └── ocr_document.py   # Internal, provider-independent OCR model
│   ├── providers/
│   │   ├── base.py           # OCRProvider interface + error types
│   │   └── google_vision.py  # GoogleVisionProvider implementation
│   ├── services/
│   │   ├── image_service.py  # Download + validate images
│   │   ├── orchestrator.py   # Per-image pipeline + response building
│   │   └── aggregator.py     # Multi-image field aggregation
│   ├── extractors/
│   │   ├── base.py
│   │   ├── price.py          # MRP extractor
│   │   ├── quantity.py       # Net quantity extractor
│   │   ├── dates.py          # MFD/PKD/EXP/Best Before extractor
│   │   └── manufacturer.py   # Manufacturer/Packer/Marketer/Importer
│   ├── utils/normalization.py
│   └── dependencies.py       # DI wiring for FastAPI
├── tests/
│   ├── test_extractors.py
│   ├── test_aggregator.py
│   ├── test_api.py
│   └── fixtures/             # FakeOCRProvider, FakeImageService
├── requirements.txt
├── .env.example
└── README.md
```

## 5. Installation

```bash
git clone <repo-url>
cd ocr_service
```

## 6. Virtual Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 7. Google Cloud Vision Setup

1. Create/select a GCP project and enable the **Cloud Vision API**.
2. Create a service account with the `Cloud Vision API User` role.
3. Download its JSON key file (keep it out of version control).
4. Point the standard environment variable at it:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/service-account.json"
```

The Google client library reads this variable automatically — no other
wiring is required.

## 8. Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `MAX_IMAGES` | `5` | Max images accepted per scan request |
| `IMAGE_DOWNLOAD_TIMEOUT` | `15` | Seconds before an image download times out |
| `MAX_IMAGE_SIZE_MB` | `10` | Max size of a single downloaded image |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Path to GCP service account JSON |
| `LOG_LEVEL` | `INFO` | Python logging level |

Never commit a populated `.env` or credential JSON file.

## 9. Running Locally

```bash
uvicorn app.main:app --reload --port 8000
```

Docs available at `http://localhost:8000/docs`.

## 10. Running Tests

```bash
pytest
```

Tests use `FakeOCRProvider` and `FakeImageService` (see `tests/fixtures/`)
via FastAPI dependency overrides — **no real Google credentials, network
access, database, or frontend are required.**

## 11. API Endpoints

### `GET /health`
```json
{ "status": "ok" }
```

### `POST /ocr/scan`
Accepts 1–`MAX_IMAGES` image URLs and returns extracted candidates.

## 12. Example Request

```json
{
  "scan_id": "scan_001",
  "images": [
    { "image_id": "front", "image_url": "https://example.com/front.jpg" },
    { "image_id": "back", "image_url": "https://example.com/back.jpg" }
  ]
}
```

## 13. Example Response

```json
{
  "scan_id": "scan_001",
  "status": "success",
  "summary": { "images_received": 2, "images_processed": 2, "images_failed": 0 },
  "images": [
    { "image_id": "front", "status": "success", "text_detected": true, "raw_text": "MRP ₹50 ...", "error": null },
    { "image_id": "back", "status": "success", "text_detected": true, "raw_text": "Net Wt. 500g ...", "error": null }
  ],
  "fields": {
    "mrp": {
      "status": "found",
      "candidates": [
        { "raw_text": "MRP ₹50", "normalized_value": 50, "currency": "INR", "confidence": "HIGH", "source_image_id": "front", "bounding_box": null }
      ]
    },
    "net_quantity": {
      "status": "found",
      "candidates": [
        { "raw_text": "Net Wt. 500g", "value": 500, "unit": "g", "confidence": "HIGH", "source_image_id": "back", "bounding_box": null }
      ]
    },
    "date_declarations": { "status": "not_found", "candidates": [] },
    "manufacturer_declarations": { "status": "not_found", "candidates": [] }
  },
  "errors": []
}
```

## 14. Important Limitations

- **Physical font size cannot reliably be determined from arbitrary image
  pixels without calibration** (known camera distance, DPI, or a reference
  object). This service does not attempt it.
- **The OCR module extracts information; the Legal Rule Engine decides
  compliance.** No legal judgment is made here — including on date validity,
  font-size sufficiency, or declaration completeness.
- OCR extraction is heuristic and regex-based by design (for MVP
  explainability/debuggability). It will miss unusual layouts or heavily
  degraded images — this is expected and acceptable for the current stage.
- Conflicting values across multiple images of the same product are
  **never resolved automatically** — both/all candidates are returned for
  a human or the rule engine to reconcile.
- Ambiguous dates (e.g. plain `DD/MM/YY`-style three-part dates with no 
  other context) are intentionally **not** normalized — `normalized_value`
  stays `null` rather than guessing a format.
- Image processing across multiple images in one request is sequential,
  not concurrent, to keep the initial implementation simple and reliable.
- Only Google Cloud Vision is supported as an OCR provider in this MVP.

