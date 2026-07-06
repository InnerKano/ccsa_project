"""Unit tests for the Layer 1 rules engine — no database required."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.modules.analysis.rules.engine import (
    canonical_merchant,
    categorize,
    run_layer_one,
)


@dataclass
class Tx:
    date: date
    description: str
    amount: Decimal


def _monthly(description: str, amount: str, months: list[int], year: int = 2026) -> list[Tx]:
    return [Tx(date(year, m, 3), description, Decimal(amount)) for m in months]


def test_canonical_merchant_maps_known_brands() -> None:
    assert canonical_merchant("NETFLIX.COM *SF") == "NETFLIX"
    assert canonical_merchant("SPOTIFY USA") == "SPOTIFY"
    assert canonical_merchant("NETFLIX BOGOTA") == "NETFLIX"


def test_canonical_merchant_reduces_unknown_noise() -> None:
    # Store numbers dropped, grouped by leading words.
    assert canonical_merchant("SHELL OIL 4471") == "SHELL OIL"


def test_categorize_is_bilingual() -> None:
    assert categorize("NETFLIX.COM") == "streaming"
    assert categorize("SPOTIFY USA") == "music"
    assert categorize("PAYROLL DEPOSIT") == "income"
    assert categorize("PAGO NOMINA") == "income"
    assert categorize("EXITO SUPERMERCADO") == "groceries"
    assert categorize("WHOLE FOODS MARKET") == "groceries"
    assert categorize("SOMETHING RANDOM XYZ") == "other"


def test_detects_recurring_subscriptions_and_savings() -> None:
    transactions = [
        *_monthly("NETFLIX.COM", "-15.49", [1, 2, 3]),
        *_monthly("SPOTIFY USA", "-10.99", [1, 2, 3]),
        *_monthly("AMAZON PRIME", "-14.99", [1, 2, 3]),
        *_monthly("PAYROLL DEPOSIT", "2450.00", [1, 2, 3]),  # income (inflow)
        Tx(date(2026, 2, 10), "SHELL OIL 4471", Decimal("-48.30")),  # one-off
    ]
    result = run_layer_one(transactions)

    merchants = {s.merchant for s in result.subscriptions}
    assert merchants == {"NETFLIX", "SPOTIFY", "AMAZON PRIME"}
    assert result.monthly_recurring_total == Decimal("41.47")
    # Only discretionary categories (streaming, music) are recommended; AMAZON
    # PRIME is categorized shopping and surfaced but not auto-flagged (D16).
    assert result.estimated_savings == Decimal("26.48")
    assert {r.title for r in result.recommendations} == {
        "Review NETFLIX subscription",
        "Review SPOTIFY subscription",
    }


def test_income_is_never_a_subscription() -> None:
    transactions = _monthly("PAYROLL DEPOSIT", "2450.00", [1, 2, 3])
    result = run_layer_one(transactions)
    assert result.subscriptions == []
    assert result.monthly_recurring_total == Decimal("0.00")
    assert result.estimated_savings == Decimal("0.00")


def test_single_occurrence_of_unknown_merchant_is_not_recurring() -> None:
    # An unfamiliar merchant seen once, with no bank recurring marker, is not
    # enough evidence to call it a subscription.
    transactions = [Tx(date(2026, 1, 3), "CORNER STORE 88", Decimal("-15.49"))]
    result = run_layer_one(transactions)
    assert result.subscriptions == []


def test_single_occurrence_of_known_service_is_suspected() -> None:
    # A known subscription service on a single statement is surfaced as a
    # suspected subscription so a lone upload (= one month) still has value (D17).
    transactions = [Tx(date(2026, 1, 3), "NETFLIX.COM", Decimal("-15.49"))]
    result = run_layer_one(transactions)
    assert len(result.subscriptions) == 1
    sub = result.subscriptions[0]
    assert sub.merchant == "NETFLIX"
    assert sub.cadence == "suspected"
    # streaming is discretionary → recommended and counted toward savings.
    assert result.estimated_savings == Decimal("15.49")
    assert result.recommendations[0].title == "Review NETFLIX subscription"


def test_bank_recurring_marker_flags_single_occurrence() -> None:
    # Bank of America appends "RECURRING" on the line; trust it even once.
    transactions = [
        Tx(
            date(2026, 2, 22),
            "CHECKCARD 0221 INSTACART SUBSCRIPTION HTTPSINSTACARCA RECURRING",
            Decimal("-9.99"),
        )
    ]
    result = run_layer_one(transactions)
    assert len(result.subscriptions) == 1
    assert result.subscriptions[0].cadence == "monthly"


def test_canonical_merchant_strips_bank_noise() -> None:
    # Real BOA-style plumbing must not split one merchant into many groups.
    assert canonical_merchant("CHECKCARD 0524 GO CLEANERS TOWSON") == "GO CLEANERS TOWSON"
    assert canonical_merchant("SQ *COLDSTONE CREAM BALTIMORE") == "COLDSTONE CREAM BALTIMORE"
    assert canonical_merchant("PMNT SENT 0525 SQC CASH APP") == "SQC CASH APP"


def test_categorize_covers_us_merchants() -> None:
    assert categorize("HULU 8778244858 CA") == "streaming"
    assert categorize("MINT MOBILE8006837392CA") == "telecom"
    assert categorize("CHIPOTLE ONLINE") == "food"
    assert categorize("EXXONMOBIL 47865886 EDGEWOOD") == "fuel"
    assert categorize("GEICO INSURANCE") == "insurance"
    assert categorize("TRADER JOE'S") == "groceries"
    assert categorize("TARGET STORE 1122") == "shopping"


def test_unstable_amount_is_not_recurring() -> None:
    # Same merchant, wildly different amounts → not a stable subscription.
    transactions = [
        Tx(date(2026, 1, 3), "CORNER STORE", Decimal("-5.00")),
        Tx(date(2026, 2, 3), "CORNER STORE", Decimal("-90.00")),
    ]
    result = run_layer_one(transactions)
    assert result.subscriptions == []


def test_categories_align_with_input_order() -> None:
    transactions = [
        Tx(date(2026, 1, 3), "NETFLIX.COM", Decimal("-15.49")),
        Tx(date(2026, 1, 4), "PAYROLL DEPOSIT", Decimal("2450.00")),
    ]
    result = run_layer_one(transactions)
    assert result.categories == ["streaming", "income"]
