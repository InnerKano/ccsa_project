"""PDF detection helpers."""

from __future__ import annotations

_PDF_MAGIC = b"%PDF"


def is_pdf(raw: bytes) -> bool:
    """True when ``raw`` looks like a PDF file (magic bytes)."""
    return raw[:4] == _PDF_MAGIC
