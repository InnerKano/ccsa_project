"""Extract tabular rows from PDF pages via pdfplumber.

Bank statements often render transactions as tables even when plain-text
extraction collapses columns (see Discover samples in ``real_samples/``).
``pdfplumber`` reads visual layout; extracted rows are fed to ``columns.py``.
"""

from __future__ import annotations

import io
from contextlib import contextmanager
from typing import Iterator

import pdfplumber


@contextmanager
def open_pdf(raw: bytes) -> Iterator[pdfplumber.PDF]:
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        yield pdf


def extract_table_rows(raw: bytes) -> list[list[str]]:
    """Return all table rows found across every page (cells stripped)."""
    rows: list[list[str]] = []
    with open_pdf(raw) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if row is None:
                        continue
                    cleaned = [(cell or "").strip() for cell in row]
                    if any(cleaned):
                        rows.append(cleaned)
    return rows


def extract_page_texts(raw: bytes) -> list[str]:
    """Plain text per page — used by the line-oriented fallback parser."""
    with open_pdf(raw) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]
