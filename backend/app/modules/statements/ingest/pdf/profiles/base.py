"""Row-profile contracts for line-oriented PDF statements (D18 → D19).

Each bank/card layout is a ``RowProfile``: it decides whether it recognizes a
document and, if so, turns its page text into normalized ``LineRow`` records.
The orchestrator (``pdf/lines.py``) tries profiles in registry order and feeds
the winner's rows to the shared column mapper (``columns.py``) — the same path
CSV uploads take (D15).

Adding a new bank layout means adding a ``RowProfile`` and registering it in
``profiles/registry.py``; ``parser.py``, ``api.py``, and persistence never
change. This is the extension point D18 anticipated ("a future
``pdf/profiles/<bank>.py`` registry ... when a fourth layout appears").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

# Month names, English + Spanish (full + abbreviations), for line-start dates.
MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|mayo|jun(?:io)?|jul(?:io)?|"
    r"ago(?:sto)?|sept(?:iembre)?|set(?:iembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?)"
)


@dataclass(frozen=True)
class LineRow:
    """One extracted transaction line. ``amount`` is a signed decimal string
    (e.g. ``"-127.00"``) so ``columns.parse_amount`` handles it unchanged."""

    date: str
    description: str
    amount: str


def rows_to_table(rows: list[LineRow]) -> list[list[str]]:
    """Turn ``LineRow`` records into the ``[header, *data]`` shape ``columns.py``
    expects. Returns ``[]`` when there is nothing to map."""
    if not rows:
        return []
    header = ["date", "description", "amount"]
    return [header, *([r.date, r.description, r.amount] for r in rows)]


@runtime_checkable
class RowProfile(Protocol):
    """A per-layout line extractor. Implementations must be stateless."""

    name: str
    # Whether identical extracted rows should be collapsed. Only layouts that
    # reprint the same transaction (e.g. Capital One card ES+EN pages) set this;
    # layouts with genuine repeated charges (PNC vending) must keep them.
    dedupe: bool

    def matches(self, pages: list[str]) -> bool:
        """Cheap document-level detection (bank name / section markers)."""
        ...

    def extract(self, pages: list[str], year: int) -> list[LineRow]:
        """Return the transaction lines this profile recognizes (may be empty)."""
        ...
