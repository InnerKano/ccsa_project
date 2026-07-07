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
    # Only discretionary categories (streaming, music) are counted as savings;
    # AMAZON PRIME is categorized shopping and surfaced as a review, not a
    # cancellation (D16). No fees here → savings == subscription savings.
    assert result.estimated_savings == Decimal("26.48")
    assert result.subscription_savings == Decimal("26.48")
    assert result.avoidable_fees == Decimal("0.00")

    cancels = {r.title for r in result.recommendations if r.kind == "cancel_subscription"}
    reviews = {r.title for r in result.recommendations if r.kind == "review_subscription"}
    assert cancels == {"Review NETFLIX subscription", "Review SPOTIFY subscription"}
    # Non-discretionary recurring is now surfaced for review (fixes "only 2"), D21.
    assert reviews == {"Review recurring AMAZON PRIME charge"}


def test_fees_are_detected_and_counted_as_hard_savings() -> None:
    # Fees ("comisiones") are the second half of the brief's problem statement.
    transactions = [
        Tx(date(2026, 1, 31), "MONTHLY MAINTENANCE FEE", Decimal("-12.00")),
        Tx(date(2026, 2, 28), "MONTHLY MAINTENANCE FEE", Decimal("-12.00")),
        Tx(date(2026, 2, 20), "OVERDRAFT FEE", Decimal("-35.00")),
    ]
    result = run_layer_one(transactions)

    # Fees are transaction types, not subscriptions, so they never leak into
    # the recurring/subscription totals (D21).
    assert result.subscriptions == []
    assert result.monthly_recurring_total == Decimal("0.00")

    fee_labels = {f.label: (f.amount, f.occurrences) for f in result.fees}
    assert fee_labels == {
        "account maintenance fees": (Decimal("24.00"), 2),
        "overdraft fees": (Decimal("35.00"), 1),
    }
    assert result.avoidable_fees == Decimal("59.00")
    assert result.subscription_savings == Decimal("0.00")
    assert result.estimated_savings == Decimal("59.00")

    fee_recs = [r for r in result.recommendations if r.kind == "avoid_fee"]
    assert {r.title for r in fee_recs} == {
        "Avoid account maintenance fees",
        "Avoid overdraft fees",
    }
    assert sum(r.estimated_saving for r in fee_recs) == Decimal("59.00")


def test_savings_split_combines_fees_and_subscriptions() -> None:
    transactions = [
        *_monthly("NETFLIX.COM", "-15.49", [1, 2, 3]),  # discretionary → counted
        *_monthly("AMAZON PRIME", "-14.99", [1, 2, 3]),  # shopping → review only
        Tx(date(2026, 2, 20), "OVERDRAFT FEE", Decimal("-35.00")),  # fee → counted
    ]
    result = run_layer_one(transactions)

    assert result.subscription_savings == Decimal("15.49")
    assert result.avoidable_fees == Decimal("35.00")
    assert result.estimated_savings == Decimal("50.49")
    # AMAZON PRIME review contributes 0 to savings but is still surfaced.
    assert any(
        r.kind == "review_subscription" and r.estimated_saving == Decimal("0.00")
        for r in result.recommendations
    )


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


def test_categorize_transaction_types_bilingual() -> None:
    # Structural/type cues classify even when the merchant is unknown (D20).
    assert categorize("Zelle money sent to CLASSY BEAUTY SALON".upper()) == "transfer"
    assert categorize("ZEL FROM GLORIA SANTANA") == "transfer"
    assert categorize("Withdrawal to Fondo de Emergencia".upper()) == "transfer"
    assert categorize("TRANSFERENCIA A AHORRO") == "transfer"
    assert categorize("Withdrawal from CAPITAL ONE MOBILE PMT".upper()) == "transfer"
    assert categorize("ATM Withdrawal - CVS STORE".upper()) == "cash"
    assert categorize("RETIRO EN CAJERO") == "cash"
    assert categorize("Monthly Interest Paid".upper()) == "income"
    assert categorize("Deposit from Sueldo".upper()) == "income"
    assert categorize("IClub Fees Debit".upper()) == "fees"
    assert categorize("OVERDRAFT FEE") == "fees"


def test_categorize_boa_real_fee_lines() -> None:
    # Patterns from the redacted BOA statement (D21.1) — were missed before.
    assert categorize("PMNTUS SVC FEE DES:SERVICEFEE ID:1085846") == "fees"
    assert categorize("Wire Transfer Fee") == "fees"
    assert categorize("M&T Bank 07/10 WITHDRWL TOWSON MD FEE") == "fees"
    # Underlying wire is not a fee — only the separate fee line is.
    assert categorize("WIRE TYPE:WIRE OUT DATE:200622 TRN:2020062200681970") == "other"
    # Inflow from linked account — not a fee (bare OVERDRAFT removed from fee cues).
    assert categorize("OVERDRAFT PROTECTION FROM 4313071621145213") == "transfer"


def test_detect_boa_fee_lines_as_hard_savings() -> None:
    transactions = [
        Tx(
            date(2020, 6, 19),
            "PMNTUS SVC FEE DES:SERVICEFEE ID:1085846 INDN:MARILYN",
            Decimal("-1.50"),
        ),
        Tx(date(2020, 6, 22), "Wire Transfer Fee", Decimal("-30.00")),
        Tx(
            date(2020, 7, 10),
            "M&T Bank 07/10 #000695484 WITHDRWL M&T 7601 OSLER DR TOWSON MD FEE",
            Decimal("-2.50"),
        ),
    ]
    result = run_layer_one(transactions)

    assert result.avoidable_fees == Decimal("34.00")
    assert result.estimated_savings == Decimal("34.00")
    fee_recs = [r for r in result.recommendations if r.kind == "avoid_fee"]
    assert len(fee_recs) == 3
    assert {r.title for r in fee_recs} == {
        "Avoid service fees",
        "Avoid wire transfer fees",
        "Avoid bank fees",
    }
    by_label = {f.label: f.amount for f in result.fees}
    assert by_label == {
        "service fees": Decimal("1.50"),
        "wire transfer fees": Decimal("30.00"),
        "bank fees": Decimal("2.50"),
    }


def test_canonical_merchant_strips_structural_tokens() -> None:
    # Transaction plumbing (from/to/zelle/card/debit + ES articles) must not end
    # up in the canonical name or merge unrelated transfers (D20).
    assert canonical_merchant("Withdrawal from CAPITAL ONE MOBILE PMT") == "CAPITAL ONE"
    assert canonical_merchant("Zelle money sent to CLASSY BEAUTY SALON LLC") == "CLASSY BEAUTY SALON"
    assert canonical_merchant("2785 Debit Card Purchase Ctlp*Mill Creek") == "CTLP MILL CREEK"
    assert canonical_merchant("Withdrawal to Fondo de Emergencia XXXXXXX5449") == "FONDO EMERGENCIA"
    # Distinct internal funds no longer collapse into one "TO FONDO DE" group.
    assert canonical_merchant("Withdrawal to Fondo de Deseos") == "FONDO DESEOS"


def test_google_one_single_occurrence_is_suspected_subscription() -> None:
    # A real subscription (Google One storage) on a single statement (D17/D20).
    transactions = [
        Tx(date(2026, 6, 11), "Debit Card Purchase - GOOGLE ONE GOOGLE COM CA", Decimal("-1.99"))
    ]
    result = run_layer_one(transactions)
    assert len(result.subscriptions) == 1
    sub = result.subscriptions[0]
    assert sub.merchant == "GOOGLE ONE"
    assert sub.cadence == "suspected"
    assert sub.category == "software"
    assert result.estimated_savings == Decimal("1.99")


def test_categories_align_with_input_order() -> None:
    transactions = [
        Tx(date(2026, 1, 3), "NETFLIX.COM", Decimal("-15.49")),
        Tx(date(2026, 1, 4), "PAYROLL DEPOSIT", Decimal("2450.00")),
    ]
    result = run_layer_one(transactions)
    assert result.categories == ["streaming", "income"]
