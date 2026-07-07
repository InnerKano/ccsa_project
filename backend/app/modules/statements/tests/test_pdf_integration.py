"""PDF parser integration tests — uses local real_samples when present (never committed)."""

from pathlib import Path

import pytest

from app.modules.statements.ingest.base import InvalidStatementError, ParseOptions, UnsupportedFormatError
from app.modules.statements.ingest.registry import parse_statement

REAL_SAMPLES = Path(__file__).resolve().parents[4] / "fixtures" / "real_samples"

CAPONE_CARD = REAL_SAMPLES / "June card statement-2026-07-06T11_29_09.566Z (1).pdf"
DISCOVER = REAL_SAMPLES / "May 2026_aleatorizado.pdf"
BOA = REAL_SAMPLES / "GOV 10a - MM BOA Acct 9041 Bank Statements -Jan-2019-Apr-2021 & Checks_Redacted.pdf"
CAPONE_360 = REAL_SAMPLES / "June bank statement-2026-07-06T11_18_42.356X.pdf"
CAPONE_360_TX = REAL_SAMPLES / "June bank statement-2026-07-06T11_57_51.265Z (1).pdf"
PNC = REAL_SAMPLES / "Statement-2025-12-04.pdf"


def _parse_file(path: Path) -> list:
    raw = path.read_bytes()
    return parse_statement(raw, path.name, ParseOptions())


@pytest.mark.skipif(not CAPONE_CARD.is_file(), reason="local real sample not available")
def test_parse_real_capital_one_card_pdf() -> None:
    txs = _parse_file(CAPONE_CARD)
    assert len(txs) >= 10
    descriptions = " ".join(t.description.upper() for t in txs)
    assert "HULU" in descriptions or "AMC" in descriptions


@pytest.mark.skipif(not DISCOVER.is_file(), reason="local real sample not available")
def test_parse_real_discover_pdf() -> None:
    txs = _parse_file(DISCOVER)
    assert len(txs) >= 3


@pytest.mark.skipif(not BOA.is_file(), reason="local real sample not available")
def test_parse_real_boa_pdf() -> None:
    txs = _parse_file(BOA)
    assert len(txs) >= 20


@pytest.mark.skipif(not CAPONE_360.is_file(), reason="local real sample not available")
def test_capital_one_360_summary_only_pdf_fails_cleanly() -> None:
    # 360 savings statements may contain no transaction table — must not invent rows.
    with pytest.raises((InvalidStatementError, UnsupportedFormatError)):
        _parse_file(CAPONE_360)


@pytest.mark.skipif(not CAPONE_360_TX.is_file(), reason="local real sample not available")
def test_parse_real_capital_one_360_checking_pdf() -> None:
    # 360 *checking* statement WITH transactions (single date + Debit/Credit + balance, D19).
    txs = _parse_file(CAPONE_360_TX)
    assert len(txs) >= 20
    assert any(t.amount < 0 for t in txs) and any(t.amount > 0 for t in txs)
    descriptions = " ".join(t.description.upper() for t in txs)
    assert "SHINEPAY LAUNDRY APP" in descriptions  # wrapped description merged


@pytest.mark.skipif(not PNC.is_file(), reason="local real sample not available")
def test_parse_real_pnc_virtual_wallet_pdf() -> None:
    # PNC: date/amount/description order, section-driven sign, repeated charges (D19).
    txs = _parse_file(PNC)
    assert len(txs) >= 20
    descriptions = " ".join(t.description.upper() for t in txs)
    assert "NETFLIX" in descriptions
    # Genuine repeated identical charges are preserved (not de-duplicated).
    repeats = [t for t in txs if "CTLP" in t.description.upper()]
    assert len(repeats) >= 4
