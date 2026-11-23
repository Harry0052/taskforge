"""Decimal crossover, including the tie and the request that follows it."""

from __future__ import annotations

from decimal import Decimal

from taskforge.cost import solve_crossover, total_cost


def test_equality_at_4000_and_first_strict_saving_at_4001() -> None:
    result = solve_crossover(
        baseline_fixed=Decimal("0"),
        baseline_variable=Decimal("0.020"),
        specialist_fixed=Decimal("60"),
        specialist_variable=Decimal("0.005"),
    )
    assert result["outcome"] == "finite_crossover"
    assert result["equality_requests"] == 4000
    assert result["first_strict_saving_request"] == 4001
    assert result["verified_on_integer_volume"] is True
    assert Decimal(result["totals_at_equality"]["baseline_total"]) == Decimal("80")
    assert Decimal(result["totals_at_equality"]["specialist_total"]) == Decimal("80")
    assert Decimal(result["totals_at_first_strict_saving"]["baseline_total"]) == Decimal("80.020")
    assert Decimal(result["totals_at_first_strict_saving"]["specialist_total"]) == Decimal("80.005")
    assert total_cost(Decimal("60"), Decimal("0.005"), 3999) > total_cost(
        Decimal("0"), Decimal("0.020"), 3999
    )


def test_higher_variable_and_fixed_cost_never_breaks_even() -> None:
    result = solve_crossover(
        baseline_fixed=Decimal("10"),
        baseline_variable=Decimal("0.020"),
        specialist_fixed=Decimal("90"),
        specialist_variable=Decimal("0.030"),
    )
    assert result["outcome"] == "no_favorable_large_volume_break_even"
    assert result["equality_requests"] is None
    assert result["first_strict_saving_request"] is None


def test_non_integer_ratio_uses_the_ceiling_request() -> None:
    result = solve_crossover(
        baseline_fixed=Decimal("0"),
        baseline_variable=Decimal("0.010"),
        specialist_fixed=Decimal("60"),
        specialist_variable=Decimal("0.003"),
    )
    assert result["equality_requests"] is None
    assert result["first_strict_saving_request"] == 8572
    assert Decimal(result["totals_at_first_strict_saving"]["specialist_total"]) < Decimal(
        result["totals_at_first_strict_saving"]["baseline_total"]
    )


def test_review_price_moves_crossover_without_a_quality_input() -> None:
    frozen_quality = {"macro_f1": "0.910000", "per_class_recall": ["1", "1", "0.8", "0.9"]}
    low = _reviewed(Decimal("0.10"))
    high = _reviewed(Decimal("0.50"))
    assert low["equality_requests"] == 10000
    assert low["first_strict_saving_request"] == 10001
    assert high["outcome"] == "no_favorable_large_volume_break_even"
    assert frozen_quality == {"macro_f1": "0.910000", "per_class_recall": ["1", "1", "0.8", "0.9"]}


def _reviewed(review_price: Decimal) -> dict:
    baseline_variable = Decimal("0.015") + Decimal("0.05") * review_price
    specialist_variable = Decimal("0.004") + Decimal("0.10") * review_price
    return solve_crossover(
        baseline_fixed=Decimal("0"),
        baseline_variable=baseline_variable,
        specialist_fixed=Decimal("60"),
        specialist_variable=specialist_variable,
    )
