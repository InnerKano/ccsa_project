"""Statements HTTP routes — upload, list, detail, archive, restore, permanent delete."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.modules.statements.ingest.base import IngestError, ParseOptions
from app.modules.statements.schemas import (
    StatementDetailResponse,
    StatementResponse,
)
from app.modules.statements.services import (
    archive_statement_for_user,
    create_statement_from_upload,
    delete_statement_for_user,
    get_statement_for_user,
    list_archived_statements_for_user,
    list_statements_for_user,
    restore_statement_for_user,
)

router = APIRouter(prefix="/api/statements", tags=["statements"])

_ALLOWED_EXTENSIONS = (".csv", ".txt", ".tsv", ".pdf")


@router.post("/", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    file: UploadFile = File(...),
    date_column: str | None = Form(None),
    description_column: str | None = Form(None),
    amount_column: str | None = Form(None),
    debit_column: str | None = Form(None),
    credit_column: str | None = Form(None),
    date_format: str | None = Form(None),
    dayfirst: bool | None = Form(None),
    decimal_style: str = Form("auto"),
    currency: str = Form("USD"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatementResponse:
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a delimited export (.csv, .tsv, .txt) or bank statement (.pdf)",
        )
    if len(currency) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="currency must be a 3-letter code",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    options = ParseOptions(
        date_column=date_column,
        description_column=description_column,
        amount_column=amount_column,
        debit_column=debit_column,
        credit_column=credit_column,
        date_format=date_format,
        dayfirst=dayfirst,
        decimal_style=decimal_style,
        currency=currency,
    )
    try:
        statement = create_statement_from_upload(db, user, file.filename, content, options)
    except IngestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StatementResponse.model_validate(statement)


@router.get("/", response_model=list[StatementResponse])
def list_statements(
    archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[StatementResponse]:
    # ?archived=true returns the soft-deleted (D22) statements for the "Archived"
    # view; default returns only active ones.
    statements = (
        list_archived_statements_for_user(db, user.id)
        if archived
        else list_statements_for_user(db, user.id)
    )
    return [StatementResponse.model_validate(s) for s in statements]


@router.get("/{statement_id}", response_model=StatementDetailResponse)
def get_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatementDetailResponse:
    statement = get_statement_for_user(db, statement_id, user.id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")
    return StatementDetailResponse.model_validate(statement)


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Soft-archive (D22): hide from the client, retain server-side, reversible.

    This is the default "delete" a user triggers from the dashboard. Permanent
    erasure is the explicit ``DELETE /{id}/permanent`` below.
    """
    archived = archive_statement_for_user(db, statement_id, user.id)
    if not archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")


@router.post("/{statement_id}/restore", response_model=StatementResponse)
def restore_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatementResponse:
    """Undo an archive (D22): make the statement and its analyses visible again."""
    statement = restore_statement_for_user(db, statement_id, user.id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")
    return StatementResponse.model_validate(statement)


@router.delete("/{statement_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_statement_permanent(
    statement_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Permanent hard delete (D22, DATA_MODEL.md §4): erase the statement and all
    derived data (transactions, analyses) via schema cascade. Right to be forgotten.
    """
    deleted = delete_statement_for_user(db, statement_id, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found")
