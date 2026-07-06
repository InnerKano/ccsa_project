"""Shared column detection and tabular row → transaction parsing.

Both delimited (CSV/TSV) and PDF adapters produce ``list[list[str]]`` rows —
a header row plus data rows — then delegate here to identify *which column is
the date, description, and amount* (D15, D18). This keeps format-specific code
thin: extract rows; shared code maps columns and normalizes fields.

See ``delimited.py`` (text files) and ``pdf/`` (bank statements).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.modules.statements.ingest.base import IngestError, InvalidStatementError, ParsedTransaction, ParseOptions
from app.modules.statements.ingest.normalizers import (
    detect_dayfirst,
    normalize_description,
    parse_amount,
    parse_date,
)

# Vocabulary for inferring columns from header labels (EN + ES, D15).
DATE_CANDIDATES: tuple[str, ...] = (
    "date",
    "trans date",
    "trans. date",
    "transaction date",
    "posting date",
    "posted date",
    "post date",
    "fecha",
    "fecha transaccion",
    "fecha transacción",
    "fecha de operacion",
    "fecha de operación",
    "fecha movimiento",
    "fecha de transaccion",
    "fecha de transacción",
)
DESCRIPTION_CANDIDATES: tuple[str, ...] = (
    "description",
    "memo",
    "narrative",
    "details",
    "merchant",
    "payee",
    "concept",
    "descripcion",
    "descripción",
    "concepto",
    "detalle",
    "comercio",
    "movimiento",
    "descripcion del movimiento",
    "descripción del movimiento",
)
AMOUNT_CANDIDATES: tuple[str, ...] = (
    "amount",
    "transaction amount",
    "value",
    "total",
    "monto",
    "importe",
    "valor",
    "cantidad",
)
DEBIT_CANDIDATES: tuple[str, ...] = (
    "debit",
    "withdrawal",
    "charge",
    "debito",
    "débito",
    "cargo",
    "retiro",
    "egreso",
)
CREDIT_CANDIDATES: tuple[str, ...] = (
    "credit",
    "deposit",
    "credito",
    "crédito",
    "abono",
    "deposito",
    "depósito",
    "ingreso",
)

DEFAULT_MAX_HEADER_SCAN = 15


@dataclass(frozen=True)
class ColumnPlan:
    """Resolved indices for the three required transaction fields."""

    date_idx: int
    description_idx: int
    amount_idx: int | None
    debit_idx: int | None
    credit_idx: int | None


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(".", "")


def find_column(
    headers: list[str],
    explicit: str | None,
    candidates: tuple[str, ...],
) -> int | None:
    lookup = {normalize_header(h): i for i, h in enumerate(headers)}
    if explicit is not None:
        idx = lookup.get(normalize_header(explicit))
        if idx is None:
            raise IngestError(f"Column not found: {explicit}")
        return idx
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def build_column_plan(headers: list[str], options: ParseOptions) -> ColumnPlan:
    """Map header labels to column indices. Raises IngestError if required columns missing."""
    date_idx = find_column(headers, options.date_column, DATE_CANDIDATES)
    description_idx = find_column(headers, options.description_column, DESCRIPTION_CANDIDATES)
    amount_idx = find_column(headers, options.amount_column, AMOUNT_CANDIDATES)
    debit_idx = find_column(headers, options.debit_column, DEBIT_CANDIDATES)
    credit_idx = find_column(headers, options.credit_column, CREDIT_CANDIDATES)

    if date_idx is None or description_idx is None:
        raise IngestError(
            "Could not identify date and description columns — provide "
            "date_column and description_column"
        )
    if amount_idx is None and debit_idx is None and credit_idx is None:
        raise IngestError(
            "Could not identify an amount column — provide amount_column "
            "(or debit_column/credit_column)"
        )
    return ColumnPlan(date_idx, description_idx, amount_idx, debit_idx, credit_idx)


def locate_header_row(
    rows: list[list[str]],
    options: ParseOptions,
    *,
    max_scan: int = DEFAULT_MAX_HEADER_SCAN,
) -> tuple[int, ColumnPlan]:
    """Return the header row index and its column plan, tolerating a small preamble."""
    last_error: IngestError | None = None
    for index, row in enumerate(rows[:max_scan]):
        try:
            return index, build_column_plan(row, options)
        except IngestError as exc:
            last_error = exc
    raise last_error or IngestError("No recognizable header row found")


def cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip()


def row_amount(row: list[str], plan: ColumnPlan, style: str) -> Decimal:
    if plan.amount_idx is not None:
        return parse_amount(row[plan.amount_idx], style)

    debit = cell(row, plan.debit_idx)
    credit = cell(row, plan.credit_idx)
    if debit:
        return -abs(parse_amount(debit, style))
    if credit:
        return abs(parse_amount(credit, style))
    raise IngestError("Row has neither a debit nor a credit value")


def parse_tabular_rows(
    rows: list[list[str]],
    options: ParseOptions,
    *,
    header_index: int | None = None,
    skip_invalid_rows: bool = False,
) -> list[ParsedTransaction]:
    """Parse a header + data table into normalized transactions.

    When ``header_index`` is omitted, scans the first rows for a recognizable
    header (same behaviour as the delimited parser).
    """
    if not rows:
        raise InvalidStatementError("File is empty")

    if header_index is None:
        header_index, plan = locate_header_row(rows, options)
    else:
        plan = build_column_plan(rows[header_index], options)

    data_rows = rows[header_index + 1 :]
    if not data_rows:
        raise InvalidStatementError("No transaction rows found after the header")

    if options.dayfirst is None and options.date_format is None:
        raw_dates = [cell(r, plan.date_idx) for r in data_rows]
        dayfirst: bool | None = detect_dayfirst(raw_dates)
    else:
        dayfirst = options.dayfirst

    transactions: list[ParsedTransaction] = []
    for row in data_rows:
        try:
            tx_date = parse_date(
                cell(row, plan.date_idx),
                date_format=options.date_format,
                dayfirst=dayfirst,
            )
            description = normalize_description(cell(row, plan.description_idx))
            amount = row_amount(row, plan, options.decimal_style)
        except IngestError:
            if skip_invalid_rows:
                continue
            raise InvalidStatementError(
                "Invalid row in file — check the date, description, and amount columns"
            ) from None
        if not description:
            continue
        transactions.append(ParsedTransaction(date=tx_date, description=description, amount=amount))

    if not transactions:
        raise InvalidStatementError("File contains no valid transactions")
    return transactions
