"""Delimited transaction-export parser (CSV/TSV with real column headers).

Supported input per D15: a delimited file whose header row exposes a date, a
description, and either a single amount column or a debit/credit pair. Column
mapping is delegated to ``columns.py`` (shared with the PDF adapter, D18).
"""

from __future__ import annotations

import csv
import io

from app.modules.statements.ingest.base import IngestError, ParsedTransaction, ParseOptions
from app.modules.statements.ingest.columns import locate_header_row, parse_tabular_rows
from app.modules.statements.ingest.normalizers import decode_bytes
from app.modules.statements.ingest.pdf.detect import is_pdf

_DELIMITERS = (",", ";", "\t", "|")


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        return max(_DELIMITERS, key=first_line.count)


def read_delimited_rows(text: str) -> list[list[str]]:
    """Parse delimited text into rows (shared helper for tests)."""
    delimiter = _sniff_delimiter(text[:4096])
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [row for row in reader if any((cell or "").strip() for cell in row)]


class DelimitedStatementParser:
    name = "delimited-csv"

    def can_parse(self, raw: bytes, filename: str, options: ParseOptions) -> bool:
        if is_pdf(raw):
            return False
        try:
            text = decode_bytes(raw)
            rows = read_delimited_rows(text)
            if not rows:
                return False
            locate_header_row(rows, options)
        except IngestError:
            return False
        return True

    def parse(self, raw: bytes, options: ParseOptions) -> list[ParsedTransaction]:
        text = decode_bytes(raw)
        rows = read_delimited_rows(text)
        return parse_tabular_rows(rows, options)
