"""PDF ingestion adapter for bank/card statements (D18)."""

from app.modules.statements.ingest.pdf.parser import PdfStatementParser

__all__ = ["PdfStatementParser"]
