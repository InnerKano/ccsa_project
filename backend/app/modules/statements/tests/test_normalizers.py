"""Unit tests for field normalization — no database required."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.statements.ingest.base import IngestError
from app.modules.statements.ingest.normalizers import (
    decode_bytes,
    detect_dayfirst,
    normalize_description,
    parse_amount,
    parse_date,
)


def test_normalize_description_collapses_whitespace() -> None:
    assert normalize_description("  NETFLIX.COM   *SF  ") == "NETFLIX.COM *SF"


@pytest.mark.parametrize(
    ("raw", "style", "expected"),
    [
        ("1,234.56", "auto", Decimal("1234.56")),  # US
        ("1.234,56", "auto", Decimal("1234.56")),  # EU / LatAm
        ("-38.900,00", "auto", Decimal("-38900.00")),  # COP
        ("(25.00)", "auto", Decimal("-25.00")),  # accounting negative
        ("+ $75.00", "auto", Decimal("75.00")),  # sign prefix + currency
        ("12.34", "auto", Decimal("12.34")),
        ("1,50", "auto", Decimal("1.50")),  # single comma decimal
        ("2,500", "us", Decimal("2500")),  # thousands, forced US
    ],
)
def test_parse_amount_styles(raw: str, style: str, expected: Decimal) -> None:
    assert parse_amount(raw, style) == expected


def test_parse_amount_empty_raises() -> None:
    with pytest.raises(IngestError):
        parse_amount("   ")


@pytest.mark.parametrize(
    ("raw", "kwargs", "expected"),
    [
        ("2026-03-02", {}, date(2026, 3, 2)),  # ISO
        ("03/02/2026", {"dayfirst": False}, date(2026, 3, 2)),  # US MM/DD
        ("03/02/2026", {"dayfirst": True}, date(2026, 2, 3)),  # EU DD/MM
        ("15/04/2026", {}, date(2026, 4, 15)),  # unambiguous day > 12
        ("Sep 4 2023", {}, date(2023, 9, 4)),  # English month name
        ("4 de abril de 2026", {}, date(2026, 4, 4)),  # Spanish long form
        ("31/05/2026", {"date_format": "%d/%m/%Y"}, date(2026, 5, 31)),  # explicit format
    ],
)
def test_parse_date_formats(raw: str, kwargs: dict, expected: date) -> None:
    assert parse_date(raw, **kwargs) == expected


def test_parse_date_unrecognized_raises() -> None:
    with pytest.raises(IngestError):
        parse_date("not-a-date")


def test_detect_dayfirst_votes_by_impossible_month() -> None:
    assert detect_dayfirst(["15/04/2026", "03/02/2026"]) is True
    assert detect_dayfirst(["04/15/2026", "02/03/2026"]) is False


def test_decode_bytes_falls_back_to_latin1() -> None:
    # "Descripción" encoded as cp1252 is not valid UTF-8; decoder must recover.
    assert "Descripción" in decode_bytes("Descripción".encode("cp1252"))
