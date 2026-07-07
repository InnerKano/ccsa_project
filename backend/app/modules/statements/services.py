"""Statement persistence — orchestrates ingestion, stores normalized rows only (D4).

Parsing lives in the pluggable ``ingest`` package; this module only decides what
to persist and enforces per-user scoping on reads/deletes.
"""

from datetime import datetime, timezone
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
    # Archived statements (D22) are hidden from the owner; only active ones list.
    return (
        db.query(Statement)
        .filter(Statement.user_id == user_id, Statement.deleted_at.is_(None))
        .order_by(Statement.uploaded_at.desc())
        .all()
    )


def list_archived_statements_for_user(db: Session, user_id: UUID) -> list[Statement]:
    # The "Archived" view (D22): only soft-deleted statements, most recent first.
    return (
        db.query(Statement)
        .filter(Statement.user_id == user_id, Statement.deleted_at.is_not(None))
        .order_by(Statement.deleted_at.desc())
        .all()
    )


def get_statement_for_user(
    db: Session,
    statement_id: UUID,
    user_id: UUID,
    *,
    include_archived: bool = False,
) -> Statement | None:
    """Fetch a user's statement.

    By default archived statements are treated as absent (→ 404), so reads and
    analysis runs behave as if the client deleted it. ``include_archived=True``
    is for the restore/permanent-delete paths, which must still find it (D22).
    """
    query = db.query(Statement).filter(
        Statement.id == statement_id, Statement.user_id == user_id
    )
    if not include_archived:
        query = query.filter(Statement.deleted_at.is_(None))
    return query.first()


def archive_statement_for_user(db: Session, statement_id: UUID, user_id: UUID) -> bool:
    """Soft-delete: hide the statement from the client, retain it server-side (D22).

    Reversible via ``restore_statement_for_user``. Data is not erased — that is the
    separate ``delete_statement_for_user`` (right-to-be-forgotten, DATA_MODEL.md §4).
    """
    statement = get_statement_for_user(db, statement_id, user_id)
    if statement is None:
        return False
    statement.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def restore_statement_for_user(
    db: Session, statement_id: UUID, user_id: UUID
) -> Statement | None:
    """Undo an archive: make the statement (and its analyses) visible again (D22)."""
    statement = get_statement_for_user(db, statement_id, user_id, include_archived=True)
    if statement is None:
        return None
    statement.deleted_at = None
    db.commit()
    db.refresh(statement)
    return statement


def delete_statement_for_user(db: Session, statement_id: UUID, user_id: UUID) -> bool:
    """Permanent hard delete (cascades to transactions + analyses) — erasure (D22)."""
    statement = get_statement_for_user(db, statement_id, user_id, include_archived=True)
    if statement is None:
        return False
    db.delete(statement)
    db.commit()
    return True
