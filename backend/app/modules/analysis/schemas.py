"""Pydantic contracts for analysis endpoints — see docs/API.md."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DetectedSubscriptionResponse(BaseModel):
    merchant: str
    amount: Decimal
    cadence: str
    category: str | None

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    title: str
    detail: str
    estimated_saving: Decimal

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    id: UUID
    statement_id: UUID
    ai_enabled: bool
    monthly_recurring_total: Decimal
    estimated_savings: Decimal
    detected_subscriptions: list[DetectedSubscriptionResponse]
    recommendations: list[RecommendationResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisSummaryResponse(BaseModel):
    """List view — totals without the per-item breakdown (docs/API.md GET /api/analysis)."""

    id: UUID
    statement_id: UUID
    ai_enabled: bool
    monthly_recurring_total: Decimal
    estimated_savings: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
