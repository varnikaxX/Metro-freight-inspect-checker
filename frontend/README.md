# Metrology Verify — Legal Metrology Compliance Scanner (Frontend)

Next.js (App Router) + TypeScript + Tailwind CSS frontend for the Legal
Metrology (Packaged Commodities) Rules, 2011 compliance backend
(`legal_metrology_backend`).

## Stack

- Next.js 14 (App Router), TypeScript
- Tailwind CSS + shadcn/ui-style primitives (`components/ui`)
- Lucide React icons, Framer Motion animations
- Axios for API calls, jsPDF for client-side report export

## 1. Install

```bash
cd legal-metrology-scanner
npm install
```

## 2. Configure the backend URL

```bash
cp .env.local.example .env.local
```

`.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The frontend calls `${NEXT_PUBLIC_API_BASE_URL}/api/v1/scan` — this matches
`routers/scan.py`'s `router = APIRouter(prefix="/api/v1", ...)` in the
backend, **not** the bare `/scan` path. If you change the backend's
`API_V1_PREFIX` in `config.py`, update `lib/api.ts` to match.

## 3. Run the backend (separate terminal)

```bash
cd legal_metrology_backend
pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_URL, SUPABASE_KEY, GOOGLE_APPLICATION_CREDENTIALS
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

CORS is already permissive (`CORS_ALLOW_ORIGINS=*`) in the backend's
`.env.example`, so no extra CORS config is needed for local dev.

## 4. Run the frontend

```bash
npm run dev
```

Visit `http://localhost:3000`. You'll be redirected to `/login`.

**Demo login:** any Badge ID + a password of 4+ characters (e.g.
`OFC-1024` / `demo1234`). This is a deliberately mocked auth layer — see
"Swapping in real auth" below.

## Folder structure

```
legal-metrology-scanner/
├── app/
│   ├── layout.tsx              # fonts, AuthProvider, global bg
│   ├── page.tsx                # root: redirects to /login or /dashboard
│   ├── globals.css             # design tokens, glass/paper utilities
│   ├── login/page.tsx          # split-screen login
│   └── dashboard/page.tsx      # upload -> scanning -> results flow
├── components/
│   ├── ui/                     # button, card, badge, input, label
│   ├── layout/navbar.tsx
│   ├── auth/login-form.tsx
│   └── scanner/
│       ├── upload-panel.tsx        # drag/drop + camera + preview
│       ├── camera-capture.tsx      # getUserMedia live capture modal
│       ├── scanning-overlay.tsx    # laser-scan loading animation
│       ├── results-panel.tsx       # top-level results layout
│       ├── compliance-seal.tsx     # Pass/Violations/Review stamp badge
│       ├── field-card.tsx          # one extracted attribute
│       └── violation-banner.tsx    # violation list
├── lib/
│   ├── types.ts                # mirrors schemas.py 1:1
│   ├── api.ts                  # axios client -> POST /api/v1/scan
│   ├── field-config.ts         # field_name -> label/icon/rule ref
│   ├── pdf-export.ts           # client-side compliance report PDF
│   └── utils.ts                # cn(), date/text formatting
├── context/auth-context.tsx    # mocked session (localStorage + cookie)
└── middleware.ts                # protects /dashboard via session cookie
```

## Known gaps vs. the original brief (by design, matched to the real backend)

- **PDF export is client-side.** `pdf_report_url` exists in the schema but
  nothing in `services/supabase_client.py` populates it yet. `lib/pdf-export.ts`
  builds the report from the `ScanResponse` JSON directly. Swap this out once
  the backend generates and returns a real `pdf_report_url`.
- **No bounding-box overlay.** The OCR step (`services/ocr.py`,
  Google Cloud Vision `document_text_detection`) isn't currently returning
  coordinate data through the API, so there's nothing for a canvas overlay
  to draw. `FieldDetail`/`ViolationDetail` have no geometry fields today.
- **Extracted fields are limited to the 7 the rule engine currently checks**
  (MRP, Net Quantity, Manufacturer, Consumer Care, Mfg Date, Country of
  Origin, Common Name) — not separate Expiry/Best-Before dates or a
  structured address. `lib/field-config.ts` is written to pick up new
  `field_name` values automatically if `services/compliance.py`'s
  `FIELD_PATTERNS` is extended later.
- **Auth is mocked**, per the brief's "beautifully mocked custom login state
  if simpler" allowance — see below to swap in something real.

## Swapping in real auth (NextAuth.js or your own IdP)

The mock lives entirely in `context/auth-context.tsx`. To replace it:

1. Keep the `OfficerSession` shape (or extend it) so `Navbar` and
   `dashboard/page.tsx` keep working.
2. Replace `login()`'s body with your real call (NextAuth `signIn`, an OIDC
   redirect, or a call to your own `/auth/login`).
3. Keep setting the `lmr_session` cookie (or switch `middleware.ts` to read
   whatever session cookie your auth library sets instead).

## Scan history (not built — optional next step)

The backend also exposes `GET /api/v1/scans` (list) and
`GET /api/v1/scans/{id}` (detail), already wrapped in `lib/api.ts`
(`fetchScanHistory`, `fetchScanById`) but not yet wired to a page. A
`/dashboard/history` list view would be a natural next addition.
