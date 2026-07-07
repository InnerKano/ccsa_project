"""Line-oriented PDF transaction extraction (fallback when tables fail).

Many US card/bank statements render transactions as space-separated *lines*
rather than extractable tables. This module infers the statement year, delegates
row extraction to the per-bank profiles in ``profiles/`` (D19), and returns
normalized tabular rows for ``columns.parse_tabular_rows``.

Adding a new bank layout does not touch this file — implement a ``RowProfile``
and register it in ``profiles/registry.py``.
"""

from __future__ import annotations

import re

from app.modules.statements.ingest.pdf.profiles.base import MONTH, rows_to_table
from app.modules.statements.ingest.pdf.profiles.registry import extract_rows

# Billing / statement period → default year for month-only or MM/DD dates.
_PERIOD_YEAR = re.compile(
    rf"(?:{MONTH})\.?\s+\d{{1,2}},?\s+(\d{{4}})\s*[-–]",
    re.IGNORECASE,
)
_PERIOD_YEAR_END = re.compile(  # "Jun 1 - Jun 30, 2026" (year after the dash)
    rf"[-–]\s*(?:{MONTH})\.?\s+\d{{1,2}},\s+(\d{{4}})",
    re.IGNORECASE,
)
_PERIOD_YEAR_ALT = re.compile(
    r"(\d{4})\s*[-–]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    re.IGNORECASE,
)
_PERIOD_OPEN_CLOSE = re.compile(
    r"OPEN TO CLOSE DATE:\s*\d{2}/\d{2}/(\d{4})",
    re.IGNORECASE,
)
_PERIOD_NUMERIC = re.compile(
    r"\d{2}/\d{2}/(\d{4})\s*[-–]\s*\d{2}/\d{2}/\d{4}",
)
_PERIOD_TO = re.compile(  # PNC: "For the period 11/08/2025 to 12/05/2025"
    r"\d{2}/\d{2}/(\d{4})\s+to\s+\d{2}/\d{2}/\d{4}",
    re.IGNORECASE,
)


def infer_statement_year(pages: list[str]) -> int | None:
    """Best-effort year from statement period banners."""
    blob = "\n".join(pages)
    for pattern in (
        _PERIOD_YEAR,
        _PERIOD_YEAR_END,
        _PERIOD_YEAR_ALT,
        _PERIOD_OPEN_CLOSE,
        _PERIOD_NUMERIC,
        _PERIOD_TO,
    ):
        match = pattern.search(blob)
        if match:
            return int(match.group(1))
    return None


def extract_line_rows(pages: list[str]) -> list[list[str]]:
    """Scan page texts and return ``[header, ...data]`` rows for ``columns.py``."""
    year = infer_statement_year(pages)
    if year is None:
        from datetime import date as date_cls

        year = date_cls.today().year

    return rows_to_table(extract_rows(pages, year))


def dedupe_rows(rows: list[list[str]]) -> list[list[str]]:
    """Drop duplicate data rows (e.g. bilingual Capital One statements)."""
    if len(rows) < 2:
        return rows
    header, *data = rows
    seen: set[tuple[str, ...]] = set()
    unique: list[list[str]] = []
    for row in data:
        key = tuple(cell.strip() for cell in row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return [header, *unique]
