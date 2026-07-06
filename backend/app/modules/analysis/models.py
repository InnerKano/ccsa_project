"""Analysis ORM models — see docs/DATA_MODEL.md §2 (`analyses`, `detected_subscriptions`, `recommendations`).

The result of running the Layer 1 (rules) pipeline on a statement. Re-running
appends a new ``Analysis`` row rather than replacing the previous one (D10);
"current" result = latest by ``created_at``.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalized for fast per-user scoping (DATA_MODEL.md §2, §7).
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # False when Layer 2 (LLM) is disabled or failed — MVP is rules-only (D2).
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # `rules` or `llm` — app-validated vocabulary, not a DB enum (D9).
    layer_used: Mapped[str] = mapped_column(String(16), nullable=False)
    monthly_recurring_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_savings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    detected_subscriptions: Mapped[list["DetectedSubscription"]] = relationship(
        "DetectedSubscription", back_populates="analysis", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="analysis", cascade="all, delete-orphan"
    )


class DetectedSubscription(Base):
    __tablename__ = "detected_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Canonical merchant derived from transaction descriptions at analysis time (D7).
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cadence: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    analysis: Mapped["Analysis"] = relationship(
        "Analysis", back_populates="detected_subscriptions"
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(String(1024), nullable=False)
    estimated_saving: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    analysis: Mapped["Analysis"] = relationship(
        "Analysis", back_populates="recommendations"
    )
