"""Unit tests for PDF line extraction — no database, no real PII required."""

from decimal import Decimal

from app.modules.statements.ingest.base import ParseOptions
from app.modules.statements.ingest.columns import parse_tabular_rows
from app.modules.statements.ingest.pdf.detect import is_pdf
from app.modules.statements.ingest.pdf.lines import dedupe_rows, extract_line_rows, infer_statement_year


def test_is_pdf_magic_bytes() -> None:
    assert is_pdf(b"%PDF-1.4\n")
    assert not is_pdf(b"date,description,amount\n")


def test_infer_statement_year_from_period_banner() -> None:
    pages = ["Savor Credit Card", "may 17, 2026 - jun 15, 2026 | 30 days"]
    assert infer_statement_year(pages) == 2026


def test_extract_capital_one_style_lines() -> None:
    pages = [
        """
may 17, 2026 - jun 15, 2026
NAME#NUM: Transactions
Fecha de Fecha de Descripción Cantidad
Transacción Registro
may 17 may 18 AMC 9640 ONLINELEAWOODKS $27.99
may 21 may 21 MINT MOBILE8006837392CA $225.77
NAME#NUM: Payments, Credits and Adjustments
may 24 may 25 CAPITAL ONE MOBILE PYMT - $200.00
jun 10 jun 10 Hulu8778244858CA $2.99
"""
    ]
    rows = extract_line_rows(pages)
    assert rows[0] == ["date", "description", "amount"]
    txs = parse_tabular_rows(rows, ParseOptions(), header_index=0)
    merchants = {t.description for t in txs}
    assert "AMC 9640 ONLINELEAWOODKS" in merchants
    assert "Hulu8778244858CA" in merchants
    amc = next(t for t in txs if "AMC" in t.description)
    assert amc.amount == Decimal("-27.99")
    payment = next(t for t in txs if "CAPITAL ONE MOBILE PYMT" in t.description)
    assert payment.amount == Decimal("200.00")


def test_extract_boa_style_lines() -> None:
    pages = [
        """
MARILYN JAMES MOSBY | Account # | May 15, 2019 to June 12, 2019
Withdrawals and other subtractions
Date Description Amount
05/28/19 CHECKCARD 0524 GO CLEANERS TOWSON MD -112.10
05/29/19 BMWFINANCIAL SVS DES:BMWFS PYMT -943.91
Deposits and other additions
08/14/20 MAYOR AND CITY C DES:DIR DEP 5549.53
"""
    ]
    rows = extract_line_rows(pages)
    txs = parse_tabular_rows(rows, ParseOptions(), header_index=0)
    withdrawal = next(t for t in txs if "GO CLEANERS" in t.description)
    assert withdrawal.amount == Decimal("-112.10")
    deposit = next(t for t in txs if "MAYOR AND CITY" in t.description)
    assert deposit.amount == Decimal("5549.53")


def test_dedupe_bilingual_duplicate_rows() -> None:
    rows = [
        ["date", "description", "amount"],
        ["2026-05-17", "NETFLIX.COM", "-15.49"],
        ["2026-05-17", "NETFLIX.COM", "-15.49"],
    ]
    deduped = dedupe_rows(rows)
    assert len(deduped) == 2  # header + one row
