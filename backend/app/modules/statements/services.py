"""Statement persistence — orchestrates ingestion, stores normalized rows only (D4).

Parsing lives in the pluggable ``ingest`` package; this module only decides what
to persist and enforces per-user scoping on reads/deletes.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.statements.ingest.base import ParseOptions
from app.modules.statements.ingest.registry import parse_statement
from app.modules.statements.models import Statement, Transaction


def create_statement_from_upload(
    db: Session,
    user: User,
    filename: str,
    content: bytes,
    options: ParseOptions,
) -> Statement:
    parsed = parse_statement(content, filename, options)
    statement = Statement(
        user_id=user.id,
        filename=filename,
        currency=options.currency.upper(),
        transaction_count=len(parsed),
    )
    db.add(statement)
    db.flush()

    for tx in parsed:
        db.add(
            Transaction(
                statement_id=statement.id,
                date=tx.date,
                description=tx.description,
                amount=tx.amount,
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
