"""Decimal lifecycle cost and the integer request where a specialist starts saving.

Measured timings never enter this module. Callers pass analyst-supplied or
already-modeled money as Decimal values.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal
from typing import Any

from taskforge.errors import TaskForgeError


def money(value: str | Decimal) -> Decimal:
    amount = value if isinstance(value, Decimal) else Decimal(value)
    return amount


def total_cost(fixed: Decimal, variable: Decimal, requests: int) -> Decimal:
    return fixed + variable * Decimal(requests)


def solve_crossover(
    *,
    baseline_fixed: Decimal,
    baseline_variable: Decimal,
    specialist_fixed: Decimal,
    specialist_variable: Decimal,
) -> dict[str, Any]:
    """Compare the two total-cost lines and check the boundary on integer volumes."""
    additional_fixed = specialist_fixed - baseline_fixed
    variable_saving = baseline_variable - specialist_variable
    result: dict[str, Any] = {
        "additional_fixed_cost": _plain(additional_fixed),
        "baseline_variable_cost_per_request": _plain(baseline_variable),
        "specialist_variable_cost_per_request": _plain(specialist_variable),
        "variable_saving_per_request": _plain(variable_saving),
        "equality_requests": None,
        "first_strict_saving_request": None,
        "verified_on_integer_volume": False,
    }
    if variable_saving > 0 and additional_fixed <= 0:
        result["outcome"] = "already_cheaper"
        result["reason"] = (
            "The specialist's variable cost is lower and its fixed cost is not higher, "
            "so it is already cheaper at every positive volume."
        )
        result["verified_on_integer_volume"] = True
        return result
    if variable_saving <= 0 and additional_fixed >= 0:
        result["outcome"] = "no_favorable_large_volume_break_even"
        result["reason"] = (
            "The specialist costs at least as much per request and its fixed cost is not lower. "
            "No large volume makes it strictly cheaper."
        )
        result["verified_on_integer_volume"] = True
        return result
    if variable_saving <= 0 and additional_fixed < 0:
        result["outcome"] = "no_favorable_large_volume_break_even"
        result["reason"] = (
            "The specialist has a lower fixed cost but a higher variable cost, so larger "
            "volumes favor the baseline. There is no favorable large-volume break-even."
        )
        result["verified_on_integer_volume"] = True
        return result

    exact = additional_fixed / variable_saving
    if exact == exact.to_integral_value():
        equality = int(exact)
        first_strict = equality + 1
    else:
        equality = None
        first_strict = int(exact.to_integral_value(rounding=ROUND_CEILING))
    _verify_integer_boundary(
        baseline_fixed,
        baseline_variable,
        specialist_fixed,
        specialist_variable,
        equality,
        first_strict,
    )
    result["outcome"] = "finite_crossover"
    result["equality_requests"] = equality
    result["first_strict_saving_request"] = first_strict
    result["exact_ratio"] = _plain(exact)
    result["verified_on_integer_volume"] = True
    if equality is not None:
        result["totals_at_equality"] = _totals(
            baseline_fixed, baseline_variable, specialist_fixed, specialist_variable, equality
        )
    result["totals_at_first_strict_saving"] = _totals(
        baseline_fixed, baseline_variable, specialist_fixed, specialist_variable, first_strict
    )
    if equality is None:
        result["reason"] = (
            f"The cost lines meet between requests. The first integer volume with a strict "
            f"specialist saving is {first_strict}."
        )
    else:
        result["reason"] = (
            f"Totals are equal at {equality} requests. The first strict specialist saving "
            f"is request {first_strict}."
        )
    return result


def _verify_integer_boundary(
    baseline_fixed: Decimal,
    baseline_variable: Decimal,
    specialist_fixed: Decimal,
    specialist_variable: Decimal,
    equality: int | None,
    first_strict: int,
) -> None:
    if first_strict < 1:
        raise TaskForgeError(
            "crossover_check", "first strict saving must be a positive request count"
        )
    strict_base = total_cost(baseline_fixed, baseline_variable, first_strict)
    strict_spec = total_cost(specialist_fixed, specialist_variable, first_strict)
    if not strict_spec < strict_base:
        raise TaskForgeError(
            "crossover_check",
            f"specialist total {strict_spec} is not below baseline {strict_base} at {first_strict}",
        )
    if equality is not None:
        equal_base = total_cost(baseline_fixed, baseline_variable, equality)
        equal_spec = total_cost(specialist_fixed, specialist_variable, equality)
        if equal_base != equal_spec:
            raise TaskForgeError(
                "crossover_check",
                f"totals differ at the reported tie volume {equality}: {equal_base} vs {equal_spec}",
            )
        if equality >= 1:
            before_base = total_cost(baseline_fixed, baseline_variable, equality - 1)
            before_spec = total_cost(specialist_fixed, specialist_variable, equality - 1)
            if not before_spec > before_base:
                raise TaskForgeError(
                    "crossover_check",
                    f"specialist is not strictly more expensive one request before the tie ({equality - 1})",
                )
    elif first_strict >= 1:
        previous = first_strict - 1
        previous_base = total_cost(baseline_fixed, baseline_variable, previous)
        previous_spec = total_cost(specialist_fixed, specialist_variable, previous)
        if previous_spec < previous_base:
            raise TaskForgeError(
                "crossover_check",
                f"specialist is already cheaper at {previous}, before the reported first saving",
            )


def _totals(
    baseline_fixed: Decimal,
    baseline_variable: Decimal,
    specialist_fixed: Decimal,
    specialist_variable: Decimal,
    requests: int,
) -> dict[str, str]:
    baseline = total_cost(baseline_fixed, baseline_variable, requests)
    specialist = total_cost(specialist_fixed, specialist_variable, requests)
    return {
        "requests": str(requests),
        "baseline_total": _plain(baseline),
        "specialist_total": _plain(specialist),
        "specialist_minus_baseline": _plain(specialist - baseline),
    }


def _plain(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"
