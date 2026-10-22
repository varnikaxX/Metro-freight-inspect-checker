"""
services/supabase_client.py
----------------------------
Supabase client initialization plus:
  - Storage helpers (upload raw label images, retrieve public URLs)
  - CRUD helpers for scans / extracted_fields / violations tables
  - Scan history retrieval with violation counts
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from config import settings

logger = logging.getLogger("supabase_client")

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Lazily instantiate a singleton Supabase client using the service-role key."""
    global _client
    if _client is None:
        try:
            _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Could not initialize Supabase. Check that SUPABASE_URL is the "
                "project URL and SUPABASE_KEY is a valid key for that project."
            ) from exc
    return _client


def get_authenticated_user(access_token: str) -> Dict[str, Any]:
    """Validate a bearer token with Supabase Auth using the server client."""
    result = get_supabase_client().auth.get_user(access_token)
    user = getattr(result, "user", None)
    if user is None:
        raise RuntimeError("Could not validate the authenticated user.")
    return {"id": user.id}


def delete_authenticated_user(user_id: str) -> None:
    """Delete only the user already validated by the account route."""
    get_supabase_client().auth.admin.delete_user(user_id)


# ============================================================================
# Storage helpers
# ============================================================================
def upload_image_to_storage(
    file_bytes: bytes,
    filename: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload raw image bytes to the configured Supabase Storage bucket
    (default: 'raw-labels') and return the public URL.

    A UUID prefix is added to avoid filename collisions between users.
    """
    client = get_supabase_client()
    bucket = settings.SUPABASE_BUCKET_RAW

    safe_name = filename.replace(" ", "_")
    storage_path = f"{uuid.uuid4()}_{safe_name}"

    try:
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to upload image to Supabase Storage")
        raise RuntimeError(f"Storage upload failed: {exc}") from exc

    public_url_response = client.storage.from_(bucket).get_public_url(storage_path)

    # supabase-py may return either a plain string or a dict depending on version
    if isinstance(public_url_response, dict):
        public_url = public_url_response.get("publicUrl") or public_url_response.get(
            "public_url"
        )
    else:
        public_url = public_url_response

    if not public_url:
        raise RuntimeError("Could not resolve public URL for uploaded image.")

    return public_url


# ============================================================================
# CRUD: scans
# ============================================================================
def insert_scan(
    raw_image_url: str,
    user_id: Optional[str] = None,
    status: str = "PENDING",
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "raw_image_url": raw_image_url,
        "status": status,
    }
    if user_id:
        payload["user_id"] = user_id

    result = client.table("scans").insert(payload).execute()
    if not result.data:
        raise RuntimeError("Failed to insert scan record.")
    return result.data[0]


def update_scan_status(
    scan_id: str,
    status: str,
    pdf_report_url: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload: Dict[str, Any] = {"status": status}
    if pdf_report_url:
        payload["pdf_report_url"] = pdf_report_url

    result = client.table("scans").update(payload).eq("id", scan_id).execute()
    if not result.data:
        raise RuntimeError(f"Failed to update scan {scan_id}.")
    return result.data[0]


def get_scan_by_id(scan_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    result = client.table("scans").select("*").eq("id", scan_id).limit(1).execute()
    if not result.data:
        return None
    return result.data[0]


def get_scan_history(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Return scans ordered by most recent first, each annotated with its
    violation_count computed from the violations table.
    """
    client = get_supabase_client()

    scans_result = (
        client.table("scans")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    scans = scans_result.data or []

    if not scans:
        return []

    scan_ids = [s["id"] for s in scans]

    violations_result = (
        client.table("violations")
        .select("scan_id")
        .in_("scan_id", scan_ids)
        .execute()
    )
    violation_rows = violations_result.data or []

    counts: Dict[str, int] = {}
    for row in violation_rows:
        counts[row["scan_id"]] = counts.get(row["scan_id"], 0) + 1

    for scan in scans:
        scan["violation_count"] = counts.get(scan["id"], 0)
        scan["is_compliant"] = counts.get(scan["id"], 0) == 0

    return scans


def count_scans() -> int:
    client = get_supabase_client()
    result = client.table("scans").select("id", count="exact").execute()
    return result.count or 0


# ============================================================================
# CRUD: extracted_fields
# ============================================================================
def insert_extracted_fields(
    scan_id: str, fields: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if not fields:
        return []

    client = get_supabase_client()
    payload = [
        {
            "scan_id": scan_id,
            "field_name": f["field_name"],
            "field_value": f.get("field_value"),
            "is_present": f.get("is_present", False),
        }
        for f in fields
    ]
    result = client.table("extracted_fields").insert(payload).execute()
    return result.data or []


def get_fields_for_scan(scan_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    result = (
        client.table("extracted_fields")
        .select("*")
        .eq("scan_id", scan_id)
        .execute()
    )
    return result.data or []


# ============================================================================
# CRUD: violations
# ============================================================================
def insert_violations(
    scan_id: str, violations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if not violations:
        return []

    client = get_supabase_client()
    payload = [
        {
            "scan_id": scan_id,
            "rule_code": v["rule_code"],
            "description": v["description"],
        }
        for v in violations
    ]
    result = client.table("violations").insert(payload).execute()
    return result.data or []


def get_violations_for_scan(scan_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    result = (
        client.table("violations").select("*").eq("scan_id", scan_id).execute()
    )
    return result.data or []
