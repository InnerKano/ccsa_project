"""Unit tests for the delimited parser — no database required."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.statements.ingest.base import (
    InvalidStatementError,
    ParseOptions,
    UnsupportedFormatError,
)
from app.modules.statements.ingest.registry import parse_statement


def _parse(raw: bytes, **opts) -> list:
    return parse_statement(raw, "statement.csv", ParseOptions(**opts))


def test_parse_us_comma_iso_dates() -> None:
    content = b"date,description,amount\n2026-01-03,NETFLIX.COM,-15.49\n2026-01-15,PAYROLL,2450.00\n"
    rows = _parse(content)
    assert len(rows) == 2
    assert rows[0].date == date(2026, 1, 3)
    assert rows[0].description == "NETFLIX.COM"
    assert rows[0].amount == Decimal("-15.49")
    assert rows[1].amount == Decimal("2450.00")


def test_parse_spanish_semicolon_eu_amounts() -> None:
    content = (
        "Fecha;Descripción;Valor\n"
        "15/01/2026;NETFLIX BOGOTA;-38.900,00\n"
        "15/02/2026;PAGO NOMINA;3.200.000,00\n"
    ).encode("utf-8")
    rows = _parse(content)
    assert len(rows) == 2
    assert rows[0].date == date(2026, 1, 15)  # day-first auto-detected
    assert rows[0].description == "NETFLIX BOGOTA"
    assert rows[0].amount == Decimal("-38900.00")
    assert rows[1].amount == Decimal("3200000.00")


def test_parse_debit_credit_columns() -> None:
    content = (
        b"Date,Description,Debit,Credit\n"
        b"2026-01-03,COFFEE,4.50,\n"
        b"2026-01-04,REFUND,,10.00\n"
    )
    rows = _parse(content)
    assert rows[0].amount == Decimal("-4.50")  # debit → negative
    assert rows[1].amount == Decimal("10.00")  # credit → positive


def test_explicit_column_mapping_overrides_inference() -> None:
    content = b"When,What,HowMuch\n2026-01-03,COFFEE SHOP,4.50\n"
    rows = _parse(
        content,
        date_column="When",
        description_column="What",
        amount_column="HowMuch",
    )
    assert len(rows) == 1
    assert rows[0].description == "COFFEE SHOP"


def test_tolerates_leading_preamble_rows() -> None:
    content = (
        b'"My Bank Export"\n'
        b"Account: 123\n"
        b"date,description,amount\n"
        b"2026-01-03,NETFLIX,-15.49\n"
    )
    rows = _parse(content)
    assert len(rows) == 1
    assert rows[0].description == "NETFLIX"


def test_pdf_dump_single_column_is_unsupported() -> None:
    # Resembles a PDF-exported statement: one quoted column, no delimited header.
    content = (
        '"Extracto Cuenta Ahorros"\n'
        '"06/04         0014 Compra en establecimiento X    -12.500,00    646.642,03"\n'
    ).encode("utf-8")
    with pytest.raises(UnsupportedFormatError):
        _parse(content)


def test_no_valid_rows_raises() -> None:
    with pytest.raises(InvalidStatementError):
        _parse(b"date,description,amount\n")
