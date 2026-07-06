"""PDF bank-statement parser — implements ``StatementParser`` (D18).

Pipeline:
1. Extract table rows (pdfplumber) and line-oriented rows (page text scan).
2. Score each candidate by how many valid transactions ``columns.py`` produces.
3. Return the best candidate — same column mapping path as CSV (D18).

The API and persistence layers are unchanged; register here only.
"""

from __future__ import annotations

from app.modules.statements.ingest.base import (
    IngestError,
    InvalidStatementError,
    ParsedTransaction,
    ParseOptions,
)
from app.modules.statements.ingest.columns import locate_header_row, parse_tabular_rows
from app.modules.statements.ingest.pdf.detect import is_pdf
from app.modules.statements.ingest.pdf.extract import extract_page_texts, extract_table_rows
from app.modules.statements.ingest.pdf.lines import dedupe_rows, extract_line_rows

_MIN_TRANSACTIONS = 1


class PdfStatementParser:
    name = "pdf-statement"

    def can_parse(self, raw: bytes, filename: str, options: ParseOptions) -> bool:
        if not is_pdf(raw) and not (filename or "").lower().endswith(".pdf"):
            return False
        if not is_pdf(raw):
            return False
        try:
            self._best_rows(raw, options)
            return True
        except IngestError:
            return False

    def parse(self, raw: bytes, options: ParseOptions) -> list[ParsedTransaction]:
        if not is_pdf(raw):
            raise InvalidStatementError("Not a valid PDF file")
        rows = dedupe_rows(self._best_rows(raw, options))
        return parse_tabular_rows(rows, options, header_index=0, skip_invalid_rows=True)

    def _best_rows(self, raw: bytes, options: ParseOptions) -> list[list[str]]:
        """Pick the extraction strategy that yields the most valid transactions."""
        candidates: list[list[list[str]]] = []

        pages = extract_page_texts(raw)
        line_rows = extract_line_rows(pages)
        if line_rows:
            candidates.append(line_rows)

        table_rows = extract_table_rows(raw)
        if table_rows:
            try:
                locate_header_row(table_rows, options)
                candidates.append(table_rows)
            except IngestError:
                pass

        if not candidates:
            raise InvalidStatementError(
                "No transaction table or parseable lines found in this PDF. "
                "Try exporting transactions as CSV from your bank, or use Advanced "
                "column mapping if the layout is supported."
            )

        best_rows: list[list[str]] | None = None
        best_count = -1
        for rows in candidates:
            try:
                txs = parse_tabular_rows(
                    dedupe_rows(rows),
                    options,
                    header_index=0,
                    skip_invalid_rows=True,
                )
            except InvalidStatementError:
                continue
            if len(txs) > best_count:
                best_count = len(txs)
                best_rows = rows

        if best_rows is None or best_count < _MIN_TRANSACTIONS:
            raise InvalidStatementError(
                "PDF was read but no valid transactions could be mapped to "
                "date, description, and amount columns."
            )
        return best_rows
