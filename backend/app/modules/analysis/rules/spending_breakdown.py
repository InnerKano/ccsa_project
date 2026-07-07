"""Spending comparison breakdown for visualization — pure, DB-free.

Aggregates detected subscriptions by category for before/after donut charts.
The category vocabulary is open-ended (D9 grows in ``vocabulary.py``); this
module never hard-codes category names. It only imports
``DISCRETIONARY_CATEGORIES`` to simulate the D16 savings scenario (full
removal of discretionary recurring charges).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Sequence

from app.modules.analysis.rules.vocabulary import DISCRETIONARY_CATEGORIES

_CENTS = Decimal("0.01")
_PERCENT = Decimal("0.1")


class SubscriptionLike(Protocol):
    amount: Decimal
    category: str | None


@dataclass(frozen=True)
class CategorySpendSlice:
    category: str
    amount: Decimal
    percentage: Decimal


@dataclass(frozen=True)
class SpendingComparison:
    before: tuple[CategorySpendSlice, ...]
    after: tuple[CategorySpendSlice, ...]


def _normalize_category(category: str | None) -> str:
    return category if category else "other"


def _aggregate_by_category(subscriptions: Sequence[SubscriptionLike]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for sub in subscriptions:
        key = _normalize_category(sub.category)
        totals[key] += sub.amount
    return dict(totals)


def _apply_savings(before: dict[str, Decimal]) -> dict[str, Decimal]:
    """Zero out discretionary categories; essentials stay unchanged (D16)."""
    return {
        category: (Decimal("0.00") if category in DISCRETIONARY_CATEGORIES else amount)
        for category, amount in before.items()
    }


def _to_slices(
    totals: dict[str, Decimal], grand_total: Decimal
) -> tuple[CategorySpendSlice, ...]:
    if not totals:
        return ()

    slices: list[CategorySpendSlice] = []
    for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        quantized = amount.quantize(_CENTS)
        if grand_total > 0:
            pct = (quantized / grand_total * 100).quantize(_PERCENT)
        else:
            pct = Decimal("0.0")
        slices.append(
            CategorySpendSlice(category=category, amount=quantized, percentage=pct)
        )
    return tuple(slices)


def build_spending_comparison(
    subscriptions: Sequence[SubscriptionLike],
) -> SpendingComparison:
    """Build before/after category slices from detected subscriptions."""
    before_totals = _aggregate_by_category(subscriptions)
    before_grand = sum(before_totals.values(), start=Decimal("0.00")).quantize(_CENTS)

    after_totals = _apply_savings(before_totals)
    after_grand = sum(after_totals.values(), start=Decimal("0.00")).quantize(_CENTS)

    return SpendingComparison(
        before=_to_slices(before_totals, before_grand),
        after=_to_slices(after_totals, after_grand),
    )
