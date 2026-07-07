"""Unit tests for the Capital One 360 and PNC line profiles (D19).

Synthetic, PII-free page text — no database, no real statements required.
Real bank samples are exercised (locally) in ``test_pdf_integration.py``.
"""

from decimal import Decimal

from app.modules.statements.ingest.base import ParseOptions
from app.modules.statements.ingest.columns import parse_tabular_rows
from app.modules.statements.ingest.pdf.lines import extract_line_rows, infer_statement_year


def _parse(pages: list[str]):
    rows = extract_line_rows(pages)
    assert rows and rows[0] == ["date", "description", "amount"]
    return parse_tabular_rows(rows, ParseOptions(), header_index=0)


# --- Capital One 360 checking -------------------------------------------------

CAPONE_360_PAGES = [
    """
STATEMENT PERIOD
Jun 1 - Jun 30, 2026
Sample Account - 36349161926
360 CHECKING
DATE DESCRIPTION CATEGORY AMOUNT BALANCE
Jun 1 Opening Balance $2,043.72
Jun 1 Withdrawal from EXAMPLE CLUB Debit - $127.00 $1,916.72
Jun 1 Deposit from Payroll XXXXXXX2016 Credit + $4,648.44 $6,565.16
Jun 2 Interest Rate Change from 3.057% to 2.960% $2,177.77
Jun 9 Debit Card Purchase - SAMPLE LAUNDRY APP
Jun 9 Debit - $25.35 $6,539.81
Jun 15 ATM Withdrawal - SAMPLE STORE #0-SD3
NORTHRIDGE, CA Debit - $80.00 $6,459.81
Jun 30 Monthly Interest Paid Credit + $0.10 $6,459.91
Jun 30 Closing Balance $6,459.91
"""
]


def test_capital_one_360_year_from_period_banner() -> None:
    assert infer_statement_year(CAPONE_360_PAGES) == 2026


def test_capital_one_360_extracts_transactions_with_correct_signs() -> None:
    txs = _parse(CAPONE_360_PAGES)
    by_desc = {t.description: t for t in txs}

    # Opening/Closing Balance and "Interest Rate Change" are not transactions.
    assert "Opening Balance" not in by_desc
    assert all("Interest Rate Change" not in t.description for t in txs)

    assert by_desc["Withdrawal from EXAMPLE CLUB"].amount == Decimal("-127.00")
    assert by_desc["Deposit from Payroll XXXXXXX2016"].amount == Decimal("4648.44")
    assert by_desc["Monthly Interest Paid"].amount == Decimal("0.10")
    assert str(by_desc["Withdrawal from EXAMPLE CLUB"].date) == "2026-06-01"


def test_capital_one_360_merges_wrapped_descriptions() -> None:
    txs = _parse(CAPONE_360_PAGES)
    laundry = next(t for t in txs if "SAMPLE LAUNDRY APP" in t.description)
    assert laundry.amount == Decimal("-25.35")
    assert laundry.description == "Debit Card Purchase - SAMPLE LAUNDRY APP"

    atm = next(t for t in txs if "SAMPLE STORE" in t.description)
    assert atm.amount == Decimal("-80.00")
    assert "NORTHRIDGE, CA" in atm.description  # continuation line merged


# --- PNC Virtual Wallet -------------------------------------------------------

PNC_PAGES = [
    """
Virtual Wallet Spend Statement
For the period 11/08/2025 to 12/05/2025
PNC Bank
Deposits and Other Additions There were 2 Deposits
Additions totaling $1,182.50.
Date Amount Description
11/14 1,052.50 Direct Deposit - Payroll Example Co
690387
11/19 130.00 Transfer From Sample Person
Banking/Debit Card Withdrawals and Purchases There were 4 Debit Card
purchases totaling $33.10.
Date Amount Description
11/10 2.15 2785 Debit Card Purchase Ctlp*Mill Creek
Bevera
11/19 26.65 2785 Recurring Debit Card Netflix, Inc.
12/01 2.15 2785 Debit Card Purchase Ctlp*Mill Creek
12/01 2.15 2785 Debit Card Purchase Ctlp*Mill Creek
Online and Electronic Banking Deductions There were 1 Online
Banking Deductions totaling $50.00.
Date Amount Description
11/17 50.00 Ach Tel Handset Sample Telco
Daily Balance Detail
Date Balance Date Balance
11/08 69.15 11/14 340.24
"""
]


def test_pnc_year_from_period_banner() -> None:
    assert infer_statement_year(PNC_PAGES) == 2025


def test_pnc_sign_follows_section() -> None:
    txs = _parse(PNC_PAGES)
    by_desc = {t.description: t for t in txs}
    # Amount column comes BEFORE description; sign implied by the section.
    assert by_desc["Direct Deposit - Payroll Example Co"].amount == Decimal("1052.50")
    assert by_desc["2785 Recurring Debit Card Netflix, Inc."].amount == Decimal("-26.65")
    assert by_desc["Ach Tel Handset Sample Telco"].amount == Decimal("-50.00")
    assert str(by_desc["Transfer From Sample Person"].date) == "2025-11-19"


def test_pnc_keeps_repeated_identical_charges() -> None:
    txs = _parse(PNC_PAGES)
    ctlp = [t for t in txs if "Ctlp*Mill Creek" in t.description]
    # 11/10 + two 12/01 charges: genuine repeats must not be de-duplicated.
    assert len(ctlp) == 3
    assert sum(1 for t in ctlp if str(t.date) == "2025-12-01") == 2


def test_pnc_excludes_daily_balance_rows() -> None:
    txs = _parse(PNC_PAGES)
    # "11/08 69.15" is a balance, not a transaction.
    assert all(t.amount != Decimal("69.15") for t in txs)
    assert len(txs) == 7
