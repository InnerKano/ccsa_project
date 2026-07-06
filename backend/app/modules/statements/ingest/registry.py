"""Parser selection — the single place new format adapters plug in.

To add support for a new input (e.g. a PDF-statement-dump parser or a
bank-specific profile), implement ``StatementParser`` and append an instance to
``_PARSERS``. The service and API layers never change.
"""

from __future__ import annotations

from app.modules.statements.ingest.base import (
    ParsedTransaction,
    ParseOptions,
    StatementParser,
    UnsupportedFormatError,
)
from app.modules.statements.ingest.delimited import DelimitedStatementParser

_PARSERS: list[StatementParser] = [
    DelimitedStatementParser(),
]


def parse_statement(raw: bytes, filename: str, options: ParseOptions) -> list[ParsedTransaction]:
    for parser in _PARSERS:
        if parser.can_parse(raw, filename, options):
            return parser.parse(raw, options)
    raise UnsupportedFormatError(
        "Unrecognized statement format. Upload a delimited transaction export "
        "(with columns for date, description, and amount). Raw PDF/bank-statement "
        "dumps are not supported yet."
    )
