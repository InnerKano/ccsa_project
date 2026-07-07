"""Unit tests for spending comparison breakdown — no database required."""

from dataclasses import dataclass
from decimal import Decimal

from app.modules.analysis.rules.spending_breakdown import build_spending_comparison


@dataclass
class Sub:
    amount: Decimal
    category: str | None


def _slice_map(slices: tuple) -> dict[str, Decimal]:
    return {s.category: s.amount for s in slices}


def _percentage_map(slices: tuple) -> dict[str, Decimal]:
    return {s.category: s.percentage for s in slices}


def test_sample_csv_breakdown_matches_d16() -> None:
    subscriptions = [
        Sub(Decimal("15.49"), "streaming"),
        Sub(Decimal("10.99"), "music"),
        Sub(Decimal("14.99"), "shopping"),
    ]
    result = build_spending_comparison(subscriptions)

    assert _slice_map(result.before) == {
        "shopping": Decimal("14.99"),
        "streaming": Decimal("15.49"),
        "music": Decimal("10.99"),
    }
    assert _slice_map(result.after) == {
        "shopping": Decimal("14.99"),
        "streaming": Decimal("0.00"),
        "music": Decimal("0.00"),
    }
    assert sum(_slice_map(result.before).values()) == Decimal("41.47")
    assert sum(_slice_map(result.after).values()) == Decimal("14.99")


def test_before_sorted_descending_by_amount() -> None:
    subscriptions = [
        Sub(Decimal("15.49"), "streaming"),
        Sub(Decimal("10.99"), "music"),
        Sub(Decimal("14.99"), "shopping"),
    ]
    result = build_spending_comparison(subscriptions)

    assert [s.category for s in result.before] == ["streaming", "shopping", "music"]


def test_percentages_sum_to_one_hundred_for_before() -> None:
    subscriptions = [
        Sub(Decimal("15.49"), "streaming"),
        Sub(Decimal("10.99"), "music"),
        Sub(Decimal("14.99"), "shopping"),
    ]
    result = build_spending_comparison(subscriptions)

    pct_total = sum(_percentage_map(result.before).values())
    assert pct_total == Decimal("100.0")


def test_null_category_groups_as_other() -> None:
    subscriptions = [Sub(Decimal("9.99"), None)]
    result = build_spending_comparison(subscriptions)

    assert len(result.before) == 1
    assert result.before[0].category == "other"
    assert result.before[0].amount == Decimal("9.99")
    assert result.after[0].amount == Decimal("9.99")


def test_empty_subscriptions_returns_empty_slices() -> None:
    result = build_spending_comparison([])

    assert result.before == ()
    assert result.after == ()


def test_aggregates_multiple_subscriptions_per_category() -> None:
    subscriptions = [
        Sub(Decimal("15.49"), "streaming"),
        Sub(Decimal("12.00"), "streaming"),
        Sub(Decimal("50.00"), "utilities"),
    ]
    result = build_spending_comparison(subscriptions)

    assert _slice_map(result.before)["streaming"] == Decimal("27.49")
    assert _slice_map(result.after)["streaming"] == Decimal("0.00")
    assert _slice_map(result.after)["utilities"] == Decimal("50.00")


def test_unknown_category_is_preserved_not_hardcoded() -> None:
    """New vocabulary categories flow through without code changes here."""
    subscriptions = [Sub(Decimal("20.00"), "pet_care")]
    result = build_spending_comparison(subscriptions)

    assert result.before[0].category == "pet_care"
    assert result.after[0].category == "pet_care"
    assert result.after[0].amount == Decimal("20.00")


def test_all_essential_categories_unchanged_in_after() -> None:
    subscriptions = [
        Sub(Decimal("80.00"), "utilities"),
        Sub(Decimal("120.00"), "insurance"),
    ]
    result = build_spending_comparison(subscriptions)

    assert _slice_map(result.before) == _slice_map(result.after)
