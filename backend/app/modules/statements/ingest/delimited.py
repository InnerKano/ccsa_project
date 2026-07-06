"""Delimited transaction-export parser (CSV/TSV with real column headers).

Supported input per D15: a delimited file whose header row exposes a date, a
description, and either a single amount column or a debit/credit pair. Column
names are inferred from an English + Spanish vocabulary, or provided explicitly
via ParseOptions. Delimiter (`,`, `;`, tab, `|`) and locale (date orientation,
decimal style) are auto-detected, with caller overrides taking precedence.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from decimal import Decimal

from app.modules.statements.ingest.base import (
    IngestError,
    InvalidStatementError,
    ParsedTransaction,
    ParseOptions,
)
from app.modules.statements.ingest.normalizers import (
    decode_bytes,
    detect_dayfirst,
    normalize_description,
    parse_amount,
    parse_date,
)

_DATE_CANDIDATES = (
    "date", "transaction date", "trans date", "posting date", "posted date",
    "fecha", "fecha transaccion", "fecha transacción", "fecha de operacion",
    "fecha de operación", "fecha movimiento",
)
_DESCRIPTION_CANDIDATES = (
    "description", "memo", "narrative", "details", "merchant", "payee", "concept",
    "descripcion", "descripción", "concepto", "detalle", "comercio", "movimiento",
    "descripcion del movimiento", "descripción del movimiento",
)
_AMOUNT_CANDIDATES = (
    "amount", "transaction amount", "value", "total",
    "monto", "importe", "valor",
)
_DEBIT_CANDIDATES = ("debit", "withdrawal", "charge", "debito", "débito", "cargo", "retiro", "egreso")
_CREDIT_CANDIDATES = ("credit", "deposit", "credito", "crédito", "abono", "deposito", "depósito", "ingreso")

_DELIMITERS = (",", ";", "\t", "|")
_MAX_HEADER_SCAN = 15


@dataclass(frozen=True)
class _ColumnPlan:
    date_idx: int
    description_idx: int
    amount_idx: int | None
    debit_idx: int | None
    credit_idx: int | None


def _normalize_header(value: str) -> str:
    return value.strip().lower()


def _find_column(
    headers: list[str],
    explicit: str | None,
    candidates: tuple[str, ...],
) -> int | None:
    lookup = {_normalize_header(h): i for i, h in enumerate(headers)}
    if explicit is not None:
        idx = lookup.get(_normalize_header(explicit))
        if idx is None:
            raise IngestError(f"Column not found: {explicit}")
        return idx
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def _build_plan(headers: list[str], options: ParseOptions) -> _ColumnPlan:
    date_idx = _find_column(headers, options.date_column, _DATE_CANDIDATES)
    description_idx = _find_column(headers, options.description_column, _DESCRIPTION_CANDIDATES)
    amount_idx = _find_column(headers, options.amount_column, _AMOUNT_CANDIDATES)
    debit_idx = _find_column(headers, options.debit_column, _DEBIT_CANDIDATES)
    credit_idx = _find_column(headers, options.credit_column, _CREDIT_CANDIDATES)

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
    return _ColumnPlan(date_idx, description_idx, amount_idx, debit_idx, credit_idx)


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        return max(_DELIMITERS, key=first_line.count)


def _read_rows(text: str) -> list[list[str]]:
    delimiter = _sniff_delimiter(text[:4096])
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [row for row in reader if any((cell or "").strip() for cell in row)]


def _locate_header(rows: list[list[str]], options: ParseOptions) -> tuple[int, _ColumnPlan]:
    """Return the header row index and its column plan, tolerating a small preamble."""
    last_error: IngestError | None = None
    for index, row in enumerate(rows[:_MAX_HEADER_SCAN]):
        try:
            return index, _build_plan(row, options)
        except IngestError as exc:
            last_error = exc
    raise last_error or IngestError("No recognizable header row found")


def _row_amount(row: list[str], plan: _ColumnPlan, style: str) -> Decimal:
    if plan.amount_idx is not None:
        return parse_amount(row[plan.amount_idx], style)

    debit = _cell(row, plan.debit_idx)
    credit = _cell(row, plan.credit_idx)
    if debit:
        return -abs(parse_amount(debit, style))
    if credit:
        return abs(parse_amount(credit, style))
    raise IngestError("Row has neither a debit nor a credit value")


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip()


class DelimitedStatementParser:
    name = "delimited-csv"

    def can_parse(self, raw: bytes, filename: str, options: ParseOptions) -> bool:
        try:
            text = decode_bytes(raw)
            rows = _read_rows(text)
            if not rows:
                return False
            _locate_header(rows, options)
        except IngestError:
            return False
        return True

    def parse(self, raw: bytes, options: ParseOptions) -> list[ParsedTransaction]:
        text = decode_bytes(raw)
        rows = _read_rows(text)
        if not rows:
            raise InvalidStatementError("File is empty")

        header_index, plan = _locate_header(rows, options)
        data_rows = rows[header_index + 1 :]
        if not data_rows:
            raise InvalidStatementError("No transaction rows found after the header")

        if options.dayfirst is None and options.date_format is None:
            raw_dates = [_cell(r, plan.date_idx) for r in data_rows]
            dayfirst: bool | None = detect_dayfirst(raw_dates)
        else:
            dayfirst = options.dayfirst

        transactions: list[ParsedTransaction] = []
        for row in data_rows:
            try:
                tx_date = parse_date(
                    _cell(row, plan.date_idx),
                    date_format=options.date_format,
                    dayfirst=dayfirst,
                )
                description = normalize_description(_cell(row, plan.description_idx))
                amount = _row_amount(row, plan, options.decimal_style)
            except IngestError:
                # Never echo row content — could contain sensitive data (API.md).
                raise InvalidStatementError(
                    "Invalid row in file — check the date, description, and amount columns"
                )
            if not description:
                continue
            transactions.append(ParsedTransaction(date=tx_date, description=description, amount=amount))

        if not transactions:
            raise InvalidStatementError("File contains no valid transactions")
        return transactions
