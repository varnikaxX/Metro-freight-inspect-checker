"""Minimal connectivity check using the same settings as the FastAPI app."""

import sys

from config import settings
from supabase import create_client


def main() -> int:
    print(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"SUPABASE_KEY: {'configured' if settings.SUPABASE_KEY else 'missing'}")

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        buckets = client.storage.list_buckets()
    except Exception as exc:  # noqa: BLE001
        print(f"Supabase check failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"Supabase check succeeded; found {len(buckets)} storage bucket(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())