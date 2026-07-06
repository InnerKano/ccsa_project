"""Ingestion contracts — pluggable statement parsers.

The API and persistence layers depend only on these abstractions, never on a
concrete parser. New input formats (a PDF-statement-dump parser, bank-specific
profiles) are added by implementing ``StatementParser`` and registering it in
``registry.py`` — without touching ``api.py`` or the persistence path.

See docs/DECISIONS.md D15 (supported input = delimited transaction export;
raw PDF/statement dumps are a post-MVP adapter).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable


class IngestError(ValueError):
    """Base for ingestion failures.

    Subclasses ``ValueError`` so existing API handlers map it to HTTP 400 without
    leaking sensitive content (see docs/API.md, docs/ARCHITECTURE.md security).
    """


class UnsupportedFormatError(IngestError):
    """No registered parser recognizes the input format."""


class InvalidStatementError(IngestError):
    """The input was recognized but contained no usable transactions."""


@dataclass(frozen=True)
class ParsedTransaction:
    date: date
    description: str
    amount: Decimal


@dataclass(frozen=True)
class ParseOptions:
    """Caller-provided hints. Everything is optional; parsers infer when omitted."""

    date_column: str | None = None
    description_column: str | None = None
    amount_column: str | None = None
    debit_column: str | None = None
    credit_column: str | None = None
    date_format: str | None = None  # explicit strptime format, e.g. "%d/%m/%Y"
    dayfirst: bool | None = None  # disambiguate DD/MM vs MM/DD when auto-parsing
    decimal_style: str = "auto"  # auto | us (1,234.56) | eu (1.234,56)
    currency: str = "USD"


@runtime_checkable
class StatementParser(Protocol):
    """A format adapter. Implementations must be side-effect free and stateless."""

    name: str

    def can_parse(self, raw: bytes, filename: str, options: ParseOptions) -> bool:
        """Cheap detection: True if this parser can handle the input.

        Receives ``options`` so explicit hints (e.g. a column mapping) can make an
        otherwise-ambiguous file recognizable.
        """
        ...

    def parse(self, raw: bytes, options: ParseOptions) -> list[ParsedTransaction]:
        """Parse to normalized transactions. Raise IngestError on bad input."""
        ...
