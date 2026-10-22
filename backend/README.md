# Legal Metrology Compliance Verification — Backend (ID26034)

Backend + Database layer (Person D) for Smart India Hackathon problem
statement **ID26034: Legal Metrology (Packaged Commodities) Rules, 2011
compliance verification**.

## Stack

- **API**: FastAPI (Python 3.11+)
- **Database & Storage & Auth**: Supabase (PostgreSQL + Storage)
- **OCR**: Google Cloud Vision (`document_text_detection`)

## Project structure

```
legal_metrology_backend/
├── main.py                    # FastAPI app, CORS, health checks
├── config.py                  # env-driven settings
├── schemas.py                 # Pydantic request/response models
├── schema.sql                 # Supabase SQL Editor script (tables, RLS, storage bucket)
├── requirements.txt
├── .env.example
├── services/
│   ├── ocr.py                 # Google Cloud Vision integration
│   ├── compliance.py          # LMR 2011 rule engine (fields + violations)
│   └── supabase_client.py     # Supabase client, storage upload, CRUD
└── routers/
    └── scan.py                # /api/v1/scan, /api/v1/scans, /api/v1/scans/{id}
```

## 1. Supabase setup

1. Create a project at https://supabase.com.
2. Open **SQL Editor** → paste the full contents of `schema.sql` → **Run**.
   This creates:
   - `scans`, `extracted_fields`, `violations` tables with FKs (`on delete cascade`) and indexes
   - RLS policies (permissive defaults — tighten before production)
   - The `raw-labels` public storage bucket
3. Copy your **Project URL** and **service_role key** from
   **Project Settings → API** into `.env` (see below). The service_role key
   is required so the backend can bypass RLS for inserts — never expose it
   to the frontend.

## 2. Google Cloud Vision setup

1. Enable the **Cloud Vision API** in a Google Cloud project.
2. Create a service account with the **Cloud Vision API User** role and
   download its JSON key file.
3. Save the key file inside the project (e.g. `gcp-vision-credentials.json`)
   and point `GOOGLE_APPLICATION_CREDENTIALS` at it in `.env`.

## 3. Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then fill in SUPABASE_URL, SUPABASE_KEY, GOOGLE_APPLICATION_CREDENTIALS

uvicorn main:app --reload --host 0.0.0.0 --port 8000
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs` (Swagger UI) once running.

## 4. Endpoints

| Method | Path                        | Description                                              |
|--------|-----------------------------|-----------------------------------------------------------|
| POST   | `/api/v1/scan`               | Upload a label image → OCR → compliance check → JSON result |
| GET    | `/api/v1/scans`              | Paginated scan history with violation counts               |
| GET    | `/api/v1/scans/{scan_id}`    | Full detail (fields + violations) for one scan              |
| GET    | `/health`                    | Health check                                                |

### Example: `POST /api/v1/scan`

```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -F "file=@label_photo.jpg"
```

Response (truncated):

```json
{
  "id": "b3c1...",
  "raw_image_url": "https://<project>.supabase.co/storage/v1/object/public/raw-labels/...",
  "status": "COMPLETED",
  "extracted_fields": [
    {"field_name": "MRP", "field_value": "199.00", "is_present": true},
    {"field_name": "NET_QUANTITY", "field_value": null, "is_present": false}
  ],
  "violations": [
    {
      "rule_code": "LMR_2011_R6_1_D_NET_QTY_MISSING",
      "description": "Net quantity (in standard units of weight/measure/number) is not declared as required under Rule 6(1)(d)."
    }
  ],
  "full_text": "..."
}
```

## 5. Notes for frontend integration (Next.js)

- CORS is currently `allow_origins=["*"]` for rapid prototyping — restrict
  this to your deployed frontend origin before the final demo/submission.
- `raw_image_url` and `pdf_report_url` are public Supabase Storage URLs,
  safe to render directly in `<img>` / download links.
- The compliance rule engine (`services/compliance.py`) is regex-based for
  MVP speed; swap in an NER model later without touching the API contract.

## 6. Extending the rule engine

Add new mandatory fields by extending `FIELD_PATTERNS` and
`RULE_METADATA` in `services/compliance.py` — no other files need to
change for new LMR 2011 field checks.
