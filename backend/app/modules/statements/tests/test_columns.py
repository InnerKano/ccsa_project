"""Unit tests for shared column detection (D18)."""

import pytest

from app.modules.statements.ingest.base import IngestError, ParseOptions
from app.modules.statements.ingest.columns import build_column_plan, locate_header_row


def test_build_column_plan_infers_en_headers() -> None:
    plan = build_column_plan(
        ["Trans Date", "Post Date", "Description", "Amount"],
        ParseOptions(),
    )
    assert plan.date_idx == 0
    assert plan.description_idx == 2
    assert plan.amount_idx == 3


def test_build_column_plan_infers_es_headers() -> None:
    plan = build_column_plan(
        ["Fecha", "Descripción", "Importe"],
        ParseOptions(),
    )
    assert plan.date_idx == 0
    assert plan.description_idx == 1
    assert plan.amount_idx == 2


def test_locate_header_skips_preamble() -> None:
    rows = [
        ["Account Summary Export"],
        ["Statement Period: Jan 2026"],
        ["Trans. Date", "Post Date", "Description", "Amount"],
        ["04/02/2026", "04/03/2026", "NETFLIX.COM", "-15.49"],
    ]
    index, plan = locate_header_row(rows, ParseOptions())
    assert index == 2
    assert plan.description_idx == 2


def test_missing_amount_column_raises() -> None:
    with pytest.raises(IngestError, match="amount"):
        build_column_plan(["Date", "Description", "Category"], ParseOptions())
