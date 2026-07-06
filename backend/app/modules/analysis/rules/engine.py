"""Layer 1 (rules) analysis — no AI, no database.

Pure, side-effect-free functions that turn a statement's transactions into:
- a category per transaction (bilingual keyword/merchant rules),
- detected recurring subscriptions (canonical merchant + stable amount + cadence),
- an estimated-savings figure and actionable recommendations.

Kept independent of SQLAlchemy so it is unit-testable without Postgres and so a
future Layer 2 (LLM) enrichment can wrap these results with graceful fallback
(D2) without rewriting the rules. Inputs are duck-typed (``TransactionLike``):
any object exposing ``date``, ``description`` and ``amount``.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Protocol, Sequence

from app.modules.analysis.rules.vocabulary import (
    CATEGORY_KEYWORDS,
    DISCRETIONARY_CATEGORIES,
    MERCHANT_ALIASES,
)

_CENTS = Decimal("0.01")
# A merchant qualifies as recurring only if seen in at least this many months.
_MIN_RECURRING_MONTHS = 2
# Allowed spread between the smallest and largest charge, relative to the median,
# before we stop treating them as "the same" subscription (tolerates tax/price bumps).
_AMOUNT_SPREAD_TOLERANCE = Decimal("0.25")
_NON_ALPHANUM = re.compile(r"[^A-Z0-9ÁÉÍÓÚÑ ]")


class TransactionLike(Protocol):
    date: date
    description: str
    amount: Decimal


@dataclass(frozen=True)
class SubscriptionFinding:
    merchant: str
    amount: Decimal
    cadence: str
    category: str


@dataclass(frozen=True)
class RecommendationFinding:
    title: str
    detail: str
    estimated_saving: Decimal


@dataclass(frozen=True)
class RulesResult:
    subscriptions: list[SubscriptionFinding] = field(default_factory=list)
    recommendations: list[RecommendationFinding] = field(default_factory=list)
    monthly_recurring_total: Decimal = Decimal("0.00")
    estimated_savings: Decimal = Decimal("0.00")
    # Category per input transaction, aligned to the input order (never None here;
    # "other" is a valid terminal category once Layer 1 has run).
    categories: list[str] = field(default_factory=list)


def canonical_merchant(description: str) -> str:
    """Derive a stable, canonical merchant name from a raw bank description (D7).

    Known brands map to a fixed name; unknown merchants are reduced to their
    leading significant words (dropping store numbers, ``*`` refs, punctuation)
    so repeated charges from the same place group together.
    """
    upper = description.upper()
    for keyword, canonical, _ in MERCHANT_ALIASES:
        if keyword in upper:
            return canonical
    cleaned = _NON_ALPHANUM.sub(" ", upper)
    tokens = [token for token in cleaned.split() if not token.isdigit()]
    return " ".join(tokens[:3]).strip() or upper.strip() or "UNKNOWN"


def categorize(description: str) -> str:
    """Classify a transaction into the controlled vocabulary (bilingual)."""
    upper = description.upper()
    for keyword, _, category in MERCHANT_ALIASES:
        if keyword in upper:
            return category
    for keyword, category in CATEGORY_KEYWORDS:
        if keyword in upper:
            return category
    return "other"


def _median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    if count % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _is_stable(amounts: list[Decimal], representative: Decimal) -> bool:
    if representative <= 0:
        return False
    spread = max(amounts) - min(amounts)
    return spread <= representative * _AMOUNT_SPREAD_TOLERANCE


def _detect_subscriptions(transactions: Sequence[TransactionLike]) -> list[SubscriptionFinding]:
    """Group outflows by canonical merchant and keep the recurring ones.

    Income and other inflows (amount >= 0) are never subscriptions. A group is
    recurring when it appears in >= _MIN_RECURRING_MONTHS distinct months with a
    stable charge amount.
    """
    groups: dict[str, list[TransactionLike]] = defaultdict(list)
    for tx in transactions:
        if tx.amount >= 0:  # inflow (income, refund) — not a subscription
            continue
        groups[canonical_merchant(tx.description)].append(tx)

    findings: list[SubscriptionFinding] = []
    for merchant, group in groups.items():
        months = {(tx.date.year, tx.date.month) for tx in group}
        if len(months) < _MIN_RECURRING_MONTHS:
            continue
        amounts = [abs(tx.amount) for tx in group]
        representative = _median(amounts).quantize(_CENTS)
        if not _is_stable(amounts, representative):
            continue
        findings.append(
            SubscriptionFinding(
                merchant=merchant,
                amount=representative,
                cadence="monthly",
                category=categorize(group[0].description),
            )
        )
    findings.sort(key=lambda f: f.amount, reverse=True)
    return findings


def _build_recommendations(
    subscriptions: list[SubscriptionFinding],
) -> tuple[list[RecommendationFinding], Decimal]:
    """Recommend cancelling discretionary recurring charges (D16).

    Layer 1 has no usage data, so it does not claim a subscription is unused; it
    surfaces the discretionary recurring charges the user can review and stop.
    """
    recommendations: list[RecommendationFinding] = []
    total_savings = Decimal("0.00")
    for sub in subscriptions:
        if sub.category not in DISCRETIONARY_CATEGORIES:
            continue
        recommendations.append(
            RecommendationFinding(
                title=f"Review {sub.merchant} subscription",
                detail=(
                    f"Recurring {sub.category} charge of about "
                    f"{sub.amount} detected every month. "
                    f"Cancelling it would save about {sub.amount} per month."
                ),
                estimated_saving=sub.amount,
            )
        )
        total_savings += sub.amount
    return recommendations, total_savings.quantize(_CENTS)


def run_layer_one(transactions: Sequence[TransactionLike]) -> RulesResult:
    """Run the full rules pipeline over a statement's transactions."""
    categories = [categorize(tx.description) for tx in transactions]
    subscriptions = _detect_subscriptions(transactions)
    monthly_total = sum(
        (sub.amount for sub in subscriptions), start=Decimal("0.00")
    ).quantize(_CENTS)
    recommendations, estimated_savings = _build_recommendations(subscriptions)
    return RulesResult(
        subscriptions=subscriptions,
        recommendations=recommendations,
        monthly_recurring_total=monthly_total,
        estimated_savings=estimated_savings,
        categories=categories,
    )
