"""Pydantic contracts for statements endpoints — see docs/API.md."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class StatementResponse(BaseModel):
    id: UUID
    filename: str
    currency: str
    transaction_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: UUID
    date: date
    description: str
    amount: Decimal
    category: str | None

    model_config = {"from_attributes": True}


class StatementDetailResponse(BaseModel):
    id: UUID
    filename: str
    currency: str
    uploaded_at: datetime
    transactions: list[TransactionResponse]

    model_config = {"from_attributes": True}


class ColumnMapping(BaseModel):
    date_column: str | None = None
    description_column: str | None = None
    amount_column: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
