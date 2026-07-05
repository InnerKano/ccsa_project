"""CSV parsing and statement persistence — parse in memory, store normalized rows only (D4)."""

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.statements.models import Statement, Transaction
from app.modules.statements.schemas import ColumnMapping

_DATE_CANDIDATES = ("date", "transaction date", "trans date", "posting date", "posted date")
_DESCRIPTION_CANDIDATES = ("description", "memo", "narrative", "details", "merchant", "payee")
_AMOUNT_CANDIDATES = ("amount", "transaction amount", "debit", "credit", "charge")

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%Y/%m/%d",
    "%d/%m/%Y",
)


def normalize_description(raw: str) -> str:
    """Trim, collapse whitespace, truncate — DATA_MODEL.md §5."""
    cleaned = re.sub(r"\s+", " ", raw.strip())
    return cleaned[:512]


def _normalize_header(header: str) -> str:
    return header.strip().lower()


def _resolve_column(
    headers: list[str],
    explicit: str | None,
    candidates: tuple[str, ...],
) -> str:
    normalized = {_normalize_header(h): h for h in headers}
    if explicit is not None:
        key = _normalize_header(explicit)
        if key not in normalized:
            raise ValueError(f"Column not found: {explicit}")
        return normalized[key]
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError("Could not infer required columns — provide date_column, description_column, amount_column")


def _parse_date(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("Empty date value")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Unrecognized date format")


def _parse_amount(value: str) -> Decimal:
    text = value.strip()
    if not text:
        raise ValueError("Empty amount value")
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.replace("$", "").replace(",", "")
    if negative:
        cleaned = cleaned[1:-1]
    cleaned = cleaned.strip()
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount format") from exc
    if negative:
        amount = -amount
    return amount.quantize(Decimal("0.01"))


def parse_csv(content: bytes, mapping: ColumnMapping) -> list[tuple[date, str, Decimal]]:
    """Parse CSV bytes into normalized transaction tuples. Raises ValueError on bad input."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row")

    headers = list(reader.fieldnames)
    date_col = _resolve_column(headers, mapping.date_column, _DATE_CANDIDATES)
    desc_col = _resolve_column(headers, mapping.description_column, _DESCRIPTION_CANDIDATES)
    amount_col = _resolve_column(headers, mapping.amount_column, _AMOUNT_CANDIDATES)

    rows: list[tuple[date, str, Decimal]] = []
    for row in reader:
        if not any((v or "").strip() for v in row.values()):
            continue
        try:
            tx_date = _parse_date(row[date_col])
            description = normalize_description(row[desc_col])
            amount = _parse_amount(row[amount_col])
        except (KeyError, ValueError):
            raise ValueError("Invalid row in CSV — check date, description, and amount columns")
        if not description:
            continue
        rows.append((tx_date, description, amount))

    if not rows:
        raise ValueError("CSV contains no valid transactions")
    return rows


def create_statement_from_csv(
    db: Session,
    user: User,
    filename: str,
    content: bytes,
    mapping: ColumnMapping,
) -> Statement:
    parsed = parse_csv(content, mapping)
    statement = Statement(
        user_id=user.id,
        filename=filename,
        currency=mapping.currency.upper(),
        transaction_count=len(parsed),
    )
    db.add(statement)
    db.flush()

    for tx_date, description, amount in parsed:
        db.add(
            Transaction(
                statement_id=statement.id,
                date=tx_date,
                description=description,
                amount=amount,
            )
        )

    db.commit()
    db.refresh(statement)
    return statement


def list_statements_for_user(db: Session, user_id: UUID) -> list[Statement]:
    return (
        db.query(Statement)
        .filter(Statement.user_id == user_id)
        .order_by(Statement.uploaded_at.desc())
        .all()
    )


def get_statement_for_user(db: Session, statement_id: UUID, user_id: UUID) -> Statement | None:
    return (
        db.query(Statement)
        .filter(Statement.id == statement_id, Statement.user_id == user_id)
        .first()
    )


def delete_statement_for_user(db: Session, statement_id: UUID, user_id: UUID) -> bool:
    statement = get_statement_for_user(db, statement_id, user_id)
    if statement is None:
        return False
    db.delete(statement)
    db.commit()
    return True
