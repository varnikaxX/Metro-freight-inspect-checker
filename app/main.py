"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.include_router(router)


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """
    Convert FastAPI/Pydantic validation errors into a small,
    guaranteed-JSON-safe structure.

    We intentionally do not expose the raw `ctx` object because it
    may contain non-JSON-serializable Python exception instances.
    """
    details: list[dict[str, Any]] = []

    for error in exc.errors():
        details.append(
            {
                "location": list(error.get("loc", [])),
                "message": str(error.get("msg", "Validation error")),
                "type": str(error.get("type", "validation_error")),
            }
        )

    return details


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a stable JSON response for request validation failures."""

    details = _safe_validation_details(exc)

    logger.warning(
        "stage=request_validation status=failed path=%s details=%s",
        request.url.path,
        details,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "The request body failed validation.",
                "details": details,
            }
        },
    )