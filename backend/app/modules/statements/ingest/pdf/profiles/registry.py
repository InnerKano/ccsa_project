"""Row-profile selection — the single place new bank layouts plug in (D19).

Order matters: bank-specific profiles are tried before the generic fallback so a
recognized layout wins. ``GenericLineProfile.matches`` is always True, so it is
the last resort. A profile that matches a document but extracts nothing (e.g. a
summary-only statement) falls through to the next profile, preserving the D18
"fail cleanly, never invent rows" behaviour.
"""

from __future__ import annotations

from app.modules.statements.ingest.pdf.profiles.base import LineRow, RowProfile
from app.modules.statements.ingest.pdf.profiles.capital_one_360 import CapitalOne360Profile
from app.modules.statements.ingest.pdf.profiles.generic import GenericLineProfile
from app.modules.statements.ingest.pdf.profiles.pnc import PncProfile

PROFILES: list[RowProfile] = [
    PncProfile(),
    CapitalOne360Profile(),
    GenericLineProfile(),
]


def extract_rows(pages: list[str], year: int) -> list[LineRow]:
    for profile in PROFILES:
        if profile.matches(pages):
            rows = profile.extract(pages, year)
            if rows:
                return _dedupe(rows) if getattr(profile, "dedupe", False) else rows
    return []


def _dedupe(rows: list[LineRow]) -> list[LineRow]:
    """Collapse identical rows (bilingual reprints). Genuine repeats are kept by
    profiles that opt out via ``dedupe = False``."""
    seen: set[tuple[str, str, str]] = set()
    unique: list[LineRow] = []
    for row in rows:
        key = (row.date, row.description.strip(), row.amount)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique
