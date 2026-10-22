"""
main.py
-------
FastAPI application entrypoint for the Legal Metrology (Packaged
Commodities) Rules, 2011 Compliance Verification backend (ID26034).

Run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import account, scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend API for verifying packaged-commodity label compliance "
        "against the Legal Metrology (Packaged Commodities) Rules, 2011. "
        "Handles image ingestion, OCR (Google Cloud Vision), rule-based "
        "violation detection, and persistence via Supabase."
    ),
    version="1.0.0",
)

# ----------------------------------------------------------------------------
# CORS - permissive for hackathon integration with the Next.js frontend.
# Tighten `allow_origins` to specific domains before production deployment.
# ----------------------------------------------------------------------------
origins = (
    ["*"]
    if settings.CORS_ALLOW_ORIGINS.strip() == "*"
    else [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------
# Routers
# ----------------------------------------------------------------------------
app.include_router(scan.router)
app.include_router(account.router)


# ----------------------------------------------------------------------------
# Global error handler (safety net so unexpected exceptions still return JSON)
# ----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


# ----------------------------------------------------------------------------
# Health check
# ----------------------------------------------------------------------------
@app.get("/", tags=["health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "ok",
        "env": settings.APP_ENV,
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
