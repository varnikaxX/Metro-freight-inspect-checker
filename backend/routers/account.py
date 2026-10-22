"""Authenticated account-management endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import supabase_client as db

logger = logging.getLogger("account_router")
router = APIRouter(prefix="/api/v1/account", tags=["account"])
bearer = HTTPBearer(auto_error=False)


def authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        return db.get_authenticated_user(credentials.credentials)
    except Exception as exc:  # noqa: BLE001 - do not expose auth provider details
        logger.warning("Account authentication failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication could not be verified.") from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user: dict = Depends(authenticated_user)) -> None:
    """Delete the currently authenticated Supabase user only."""
    try:
        db.delete_authenticated_user(user["id"])
    except Exception as exc:  # noqa: BLE001 - keep provider internals server-side
        logger.exception("Account deletion failed for authenticated user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account deletion failed. Please try again.") from exc