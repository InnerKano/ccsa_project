"""Pydantic contracts for analysis endpoints — see docs/API.md."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.modules.analysis.rules.spending_breakdown import (
    CategorySpendSlice,
    SpendingComparison,
    build_spending_comparison,
)


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


class CategorySpendSliceResponse(BaseModel):
    category: str
    amount: Decimal
    percentage: Decimal


class SpendingComparisonResponse(BaseModel):
    before: list[CategorySpendSliceResponse]
    after: list[CategorySpendSliceResponse]

    @classmethod
    def from_comparison(cls, comparison: SpendingComparison) -> Self:
        return cls(
            before=[_slice_to_response(s) for s in comparison.before],
            after=[_slice_to_response(s) for s in comparison.after],
        )


def _slice_to_response(slice_: CategorySpendSlice) -> CategorySpendSliceResponse:
    return CategorySpendSliceResponse(
        category=slice_.category,
        amount=slice_.amount,
        percentage=slice_.percentage,
    )


class AnalysisResponse(BaseModel):
    id: UUID
    statement_id: UUID
    ai_enabled: bool
    monthly_recurring_total: Decimal
    estimated_savings: Decimal
    detected_subscriptions: list[DetectedSubscriptionResponse]
    recommendations: list[RecommendationResponse]
    created_at: datetime
    spending_comparison: SpendingComparisonResponse | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def attach_spending_comparison(self) -> Self:
        if self.spending_comparison is not None:
            return self
        comparison = build_spending_comparison(self.detected_subscriptions)
        return self.model_copy(
            update={"spending_comparison": SpendingComparisonResponse.from_comparison(comparison)}
        )


class AnalysisSummaryResponse(BaseModel):
    """List view — totals without the per-item breakdown (docs/API.md GET /api/analysis)."""

    id: UUID
    statement_id: UUID
    ai_enabled: bool
    monthly_recurring_total: Decimal
    estimated_savings: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
