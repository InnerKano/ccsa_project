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
    DEFAULT_FEE_LABEL,
    DISCRETIONARY_CATEGORIES,
    FEE_DESCRIPTION_KEYWORDS,
    FEE_LABELS,
    KNOWN_SUBSCRIPTIONS,
    MERCHANT_ALIASES,
    MERCHANT_NOISE_TOKENS,
    RECURRING_MARKERS,
)

_CENTS = Decimal("0.01")
# Matches a standalone FEE/FEES token (e.g. "M&T Bank … WITHDRWL … FEE") without
# hitting merchant names like "COFFEE" (no word boundary before FEE).
_FEE_WORD_RE = re.compile(r"\bFEES?\b")
# A merchant qualifies as recurring only if seen in at least this many months.
_MIN_RECURRING_MONTHS = 2
# Allowed spread between the smallest and largest charge, relative to the median,
# before we stop treating them as "the same" subscription (tolerates tax/price bumps).
_AMOUNT_SPREAD_TOLERANCE = Decimal("0.25")
_NON_ALPHANUM = re.compile(r"[^A-Z0-9ÁÉÍÓÚÑ ]")
# Transaction *types*, not merchants/services — never treated as subscriptions
# even when they repeat. Fees are surfaced by the dedicated fee path (D21); a
# recurring internal transfer or ATM withdrawal is not a service to cancel.
# Income is already excluded by sign (inflows), but a negative transfer is an
# outflow, so it is listed here explicitly.
_NON_SUBSCRIPTION_CATEGORIES = frozenset({"fees", "transfer", "cash"})

# Recommendation kinds (D21) — let the UI group and tone each item and let the
# response derive the hard-vs-potential savings split without new DB columns.
KIND_CANCEL_SUBSCRIPTION = "cancel_subscription"  # discretionary → counted savings
KIND_REVIEW_SUBSCRIPTION = "review_subscription"  # essential recurring → review only
KIND_AVOID_FEE = "avoid_fee"  # bank/card fees → counted (hard) savings


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
class FeeFinding:
    label: str
    amount: Decimal  # total charged for this fee type across the statement
    occurrences: int


@dataclass(frozen=True)
class RecommendationFinding:
    title: str
    detail: str
    estimated_saving: Decimal
    kind: str


@dataclass(frozen=True)
class RulesResult:
    subscriptions: list[SubscriptionFinding] = field(default_factory=list)
    fees: list[FeeFinding] = field(default_factory=list)
    recommendations: list[RecommendationFinding] = field(default_factory=list)
    monthly_recurring_total: Decimal = Decimal("0.00")
    # Total actionable savings = discretionary subscriptions (potential) + fees (hard).
    estimated_savings: Decimal = Decimal("0.00")
    # Potential savings from cancelling discretionary subscriptions (D16).
    subscription_savings: Decimal = Decimal("0.00")
    # Hard savings from avoidable bank/card fees already paid (D21).
    avoidable_fees: Decimal = Decimal("0.00")
    # Category per input transaction, aligned to the input order (never None here;
    # "other" is a valid terminal category once Layer 1 has run).
    categories: list[str] = field(default_factory=list)


def canonical_merchant(description: str) -> str:
    """Derive a stable, canonical merchant name from a raw bank description (D7).

    Known brands map to a fixed name; unknown merchants are reduced to their
    leading significant words so repeated charges from the same place group
    together. Real statements pad descriptions with transaction plumbing
    (``CHECKCARD 0524 ...``, ``PMNT SENT ...``, ``SQ *...``), store numbers and
    reference IDs — those are dropped here so the same merchant is not split into
    several groups (D17). Tokens that contain any digit (store #s, ref numbers,
    city/state-glued codes) and known boilerplate tokens are removed.
    """
    upper = description.upper()
    for keyword, canonical, _ in MERCHANT_ALIASES:
        if keyword in upper:
            return canonical
    cleaned = _NON_ALPHANUM.sub(" ", upper)
    tokens = [
        token
        for token in cleaned.split()
        if not any(char.isdigit() for char in token)
        and token not in MERCHANT_NOISE_TOKENS
    ]
    return " ".join(tokens[:3]).strip() or upper.strip() or "UNKNOWN"


def _has_recurring_marker(description: str) -> bool:
    """True if the bank itself flagged the line as recurring (D17)."""
    upper = description.upper()
    return any(marker in upper for marker in RECURRING_MARKERS)


def _is_fee(description: str) -> bool:
    """True when the description is a bank/card fee, not the underlying transfer (D21.1).

    Checked before the generic CATEGORY_KEYWORDS pass so "Wire Transfer Fee" is a
    fee, not a transfer, and BOA abbreviations ("SVC FEE", "SERVICEFEE") match.
    """
    upper = description.upper()
    if any(keyword in upper for keyword in FEE_DESCRIPTION_KEYWORDS):
        return True
    return bool(_FEE_WORD_RE.search(upper))


def categorize(description: str) -> str:
    """Classify a transaction into the controlled vocabulary (bilingual)."""
    upper = description.upper()
    for keyword, _, category in MERCHANT_ALIASES:
        if keyword in upper:
            return category
    if _is_fee(upper):
        return "fees"
    for keyword, category in CATEGORY_KEYWORDS:
        if keyword in upper:
            return category
    return "other"


def fee_label(description: str) -> str:
    """Map a fee charge to a human-readable fee-type label (D21)."""
    upper = description.upper()
    for keyword, label in FEE_LABELS:
        if keyword in upper:
            return label
    return DEFAULT_FEE_LABEL


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

    Income and other inflows (amount >= 0) are never subscriptions. A merchant
    group is treated as a subscription when any of these hold:

    - **strong (multi-month):** it appears in >= _MIN_RECURRING_MONTHS distinct
      months with a stable charge amount → cadence ``monthly``.
    - **bank marker:** the bank flagged a line as recurring (D17) → cadence
      ``monthly`` (the bank asserts the cadence).
    - **known service:** the canonical merchant is an inherently subscription
      service (e.g. NETFLIX, MINT MOBILE) even from a single statement → cadence
      ``suspected`` (honest: one occurrence is not proof of cadence, D17).

    This lets the analyzer produce value on a single real statement, which the
    multi-month rule alone could not (a lone upload = one month → nothing).
    """
    groups: dict[str, list[TransactionLike]] = defaultdict(list)
    for tx in transactions:
        if tx.amount >= 0:  # inflow (income, refund) — not a subscription
            continue
        if categorize(tx.description) in _NON_SUBSCRIPTION_CATEGORIES:
            continue  # fees/transfers/cash are transaction types, not services (D21)
        groups[canonical_merchant(tx.description)].append(tx)

    findings: list[SubscriptionFinding] = []
    for merchant, group in groups.items():
        amounts = [abs(tx.amount) for tx in group]
        representative = _median(amounts).quantize(_CENTS)
        if representative <= 0:
            continue

        months = {(tx.date.year, tx.date.month) for tx in group}
        multi_month = len(months) >= _MIN_RECURRING_MONTHS and _is_stable(
            amounts, representative
        )
        bank_marked = any(_has_recurring_marker(tx.description) for tx in group)
        known_service = merchant in KNOWN_SUBSCRIPTIONS

        if not (multi_month or bank_marked or known_service):
            continue

        cadence = "monthly" if (multi_month or bank_marked) else "suspected"
        findings.append(
            SubscriptionFinding(
                merchant=merchant,
                amount=representative,
                cadence=cadence,
                category=categorize(group[0].description),
            )
        )
    findings.sort(key=lambda f: f.amount, reverse=True)
    return findings


def _build_subscription_recommendations(
    subscriptions: list[SubscriptionFinding],
) -> tuple[list[RecommendationFinding], Decimal]:
    """Turn detected subscriptions into recommendations (D16, extended D21).

    Layer 1 has no usage data, so it does not claim a subscription is unused. It
    splits detected recurring charges in two:

    - **discretionary** (streaming, music, gaming, software, fitness) → an
      actionable *cancel* recommendation whose amount counts toward savings.
    - **everything else recurring** (utilities, telecom, insurance, shopping…)
      → a *review* recommendation with **zero** claimed savings, so essentials
      are surfaced ("worth reviewing / renegotiating") without overstating what
      can be saved. This is why the results are no longer limited to the handful
      of discretionary services.
    """
    recommendations: list[RecommendationFinding] = []
    total_savings = Decimal("0.00")
    for sub in subscriptions:
        if sub.category in DISCRETIONARY_CATEGORIES:
            if sub.cadence == "monthly":
                detail = (
                    f"Recurring {sub.category} charge of about "
                    f"{sub.amount} detected every month. "
                    f"Cancelling it would save about {sub.amount} per month."
                )
            else:
                detail = (
                    f"Likely {sub.category} subscription of about {sub.amount} "
                    f"found on this statement. Review it — cancelling would save "
                    f"about {sub.amount} per month."
                )
            recommendations.append(
                RecommendationFinding(
                    title=f"Review {sub.merchant} subscription",
                    detail=detail,
                    estimated_saving=sub.amount,
                    kind=KIND_CANCEL_SUBSCRIPTION,
                )
            )
            total_savings += sub.amount
        else:
            detail = (
                f"Recurring {sub.category} charge of about {sub.amount} from "
                f"{sub.merchant}. Likely essential, but worth reviewing — you may "
                f"be able to downgrade the plan or renegotiate a lower rate."
            )
            recommendations.append(
                RecommendationFinding(
                    title=f"Review recurring {sub.merchant} charge",
                    detail=detail,
                    estimated_saving=Decimal("0.00"),
                    kind=KIND_REVIEW_SUBSCRIPTION,
                )
            )
    return recommendations, total_savings.quantize(_CENTS)


def _detect_fees(transactions: Sequence[TransactionLike]) -> list[FeeFinding]:
    """Group outflow fee charges by fee type (D21).

    Unlike subscriptions, a fee needs no recurrence to be worth surfacing — any
    bank/card fee is money the consumer likely did not intend to pay, which is
    exactly the "commissions they don't know they have" from the brief. Charges
    categorized as ``fees`` are aggregated by their human-readable label so the
    user sees "you paid $X in overdraft fees" instead of one row per charge.
    """
    groups: dict[str, list[Decimal]] = defaultdict(list)
    for tx in transactions:
        if tx.amount >= 0:  # inflow — not a fee the user paid
            continue
        if categorize(tx.description) != "fees":
            continue
        groups[fee_label(tx.description)].append(abs(tx.amount))

    findings: list[FeeFinding] = []
    for label, amounts in groups.items():
        total = sum(amounts, start=Decimal("0.00")).quantize(_CENTS)
        if total <= 0:
            continue
        findings.append(FeeFinding(label=label, amount=total, occurrences=len(amounts)))
    findings.sort(key=lambda f: f.amount, reverse=True)
    return findings


def _build_fee_recommendations(
    fees: list[FeeFinding],
) -> tuple[list[RecommendationFinding], Decimal]:
    """Recommend eliminating avoidable fees; their total is hard savings (D21)."""
    recommendations: list[RecommendationFinding] = []
    total = Decimal("0.00")
    for fee in fees:
        times = "once" if fee.occurrences == 1 else f"{fee.occurrences} times"
        detail = (
            f"You paid about {fee.amount} in {fee.label} ({times} on this "
            f"statement). These charges are usually avoidable — contact your bank "
            f"or adjust your account settings to stop paying them."
        )
        recommendations.append(
            RecommendationFinding(
                title=f"Avoid {fee.label}",
                detail=detail,
                estimated_saving=fee.amount,
                kind=KIND_AVOID_FEE,
            )
        )
        total += fee.amount
    return recommendations, total.quantize(_CENTS)


def run_layer_one(transactions: Sequence[TransactionLike]) -> RulesResult:
    """Run the full rules pipeline over a statement's transactions."""
    categories = [categorize(tx.description) for tx in transactions]

    subscriptions = _detect_subscriptions(transactions)
    monthly_total = sum(
        (sub.amount for sub in subscriptions), start=Decimal("0.00")
    ).quantize(_CENTS)

    fees = _detect_fees(transactions)

    # Order recommendations by confidence of savings: avoidable fees (already
    # paid, hard) → discretionary cancellations (potential) → essential reviews.
    fee_recs, avoidable_fees = _build_fee_recommendations(fees)
    sub_recs, subscription_savings = _build_subscription_recommendations(subscriptions)
    recommendations = fee_recs + sub_recs

    estimated_savings = (avoidable_fees + subscription_savings).quantize(_CENTS)

    return RulesResult(
        subscriptions=subscriptions,
        fees=fees,
        recommendations=recommendations,
        monthly_recurring_total=monthly_total,
        estimated_savings=estimated_savings,
        subscription_savings=subscription_savings,
        avoidable_fees=avoidable_fees,
        categories=categories,
    )
