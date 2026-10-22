"""Fake image service for tests that avoids real network calls."""
from __future__ import annotations


class FakeImageService:
    """Returns dummy bytes instead of downloading from a real URL.

    Can be configured to raise a specific error for a given image_url to
    simulate download/validation failures.
    """

    def __init__(self) -> None:
        self._errors: dict[str, Exception] = {}

    def fail_for(self, image_url: str, exc: Exception) -> None:
        self._errors[image_url] = exc

    def fetch_and_validate(self, image_url: str) -> bytes:
        if image_url in self._errors:
            raise self._errors[image_url]
        return b"fake-image-bytes"
