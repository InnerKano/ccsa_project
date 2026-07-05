"""Unit tests for CSV parsing — no database required."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.statements.schemas import ColumnMapping
from app.modules.statements.services import normalize_description, parse_csv


def test_normalize_description_collapses_whitespace() -> None:
    assert normalize_description("  NETFLIX.COM   *SF  ") == "NETFLIX.COM *SF"


def test_parse_csv_default_columns() -> None:
    content = b"date,description,amount\n2026-01-15,TEST MERCHANT,12.34\n"
    rows = parse_csv(content, ColumnMapping())
    assert rows == [(date(2026, 1, 15), "TEST MERCHANT", Decimal("12.34"))]


def test_parse_csv_parentheses_amount() -> None:
    content = b"date,description,amount\n2026-01-15,REFUND,(25.00)\n"
    rows = parse_csv(content, ColumnMapping())
    assert rows[0][2] == Decimal("-25.00")


def test_parse_csv_empty_raises() -> None:
    with pytest.raises(ValueError, match="no valid transactions"):
        parse_csv(b"date,description,amount\n", ColumnMapping())
