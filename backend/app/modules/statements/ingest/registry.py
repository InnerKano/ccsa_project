"""Parser selection — the single place new format adapters plug in.

To add support for a new input (e.g. a bank-specific profile), implement
``StatementParser`` and append an instance to ``_PARSERS``. The service and API
layers never change.

Order matters: PDF is checked before delimited text so binary PDF bytes are not
mis-read as Latin-1 CSV (D18).
"""

from __future__ import annotations

from app.modules.statements.ingest.base import (
    ParsedTransaction,
    ParseOptions,
    StatementParser,
    UnsupportedFormatError,
)
from app.modules.statements.ingest.delimited import DelimitedStatementParser
from app.modules.statements.ingest.pdf.parser import PdfStatementParser

_PARSERS: list[StatementParser] = [
    PdfStatementParser(),
    DelimitedStatementParser(),
]


def parse_statement(raw: bytes, filename: str, options: ParseOptions) -> list[ParsedTransaction]:
    for parser in _PARSERS:
        if parser.can_parse(raw, filename, options):
            return parser.parse(raw, options)
    raise UnsupportedFormatError(
        "Unrecognized statement format. Upload a delimited export (CSV/TSV) "
        "or a bank/card statement PDF with a transaction table."
    )
