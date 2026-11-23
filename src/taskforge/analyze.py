"""End-to-end analysis. File loading stays here; scoring and cost stay pure."""

from __future__ import annotations

import platform
from decimal import Decimal
from pathlib import Path
from typing import Any

from taskforge.cost import money, solve_crossover
from taskforge.score import review_rate, score_predictions
from taskforge.train import predict_items, train_specialist
from taskforge.validate import (
    LABELS,
    load_json_object,
    validate_costs,
    validate_dataset,
    validate_trace,
)


def analyze_paths(dataset_path: Path, trace_path: Path, costs_path: Path) -> dict[str, Any]:
    dataset = validate_dataset(load_json_object(dataset_path))
    trace = validate_trace(load_json_object(trace_path), dataset)
    costs = validate_costs(load_json_object(costs_path))
    report = analyze_documents(dataset, trace, costs)
    report["inputs"] = {
        "dataset": str(dataset_path),
        "trace": str(trace_path),
        "costs": str(costs_path),
    }
    return report


def analyze_documents(
    dataset: dict[str, Any],
    trace: dict[str, Any],
    costs: dict[str, Any],
) -> dict[str, Any]:
    items = dataset["items"]
    train_items = [item for item in items if item["split"] == "train"]
    validation_items = [item for item in items if item["split"] == "validation"]
    evaluation_items = sorted(
        (item for item in items if item["split"] == "evaluation"),
        key=lambda item: item["item_id"],
    )
    model = train_specialist(train_items, validation_items)
    specialist_rows, eval_ms = predict_items(model, evaluation_items)
    trace_by_id = {row["item_id"]: row for row in trace["results"]}
    general_rows = []
    combined = []
    for row in specialist_rows:
        general = trace_by_id[row["item_id"]]
        general_rows.append(
            {
                "gold": row["gold"],
                "predicted_label": general["output_label"],
                "scoring_status": general["scoring_status"],
            }
        )
        combined.append(
            {
                "item_id": row["item_id"],
                "template_family": row["template_family"],
                "text": row["text"],
                "gold": row["gold"],
                "specialist_label": row["predicted_label"],
                "specialist_status": row["scoring_status"],
                "specialist_confidence": row["confidence"],
                "general_label": general["output_label"],
                "general_status": general["scoring_status"],
                "general_wall_time_ms": general["wall_time_ms"],
                "general_timeout": general["timeout"],
            }
        )
    specialist_metrics = score_predictions(specialist_rows)
    general_metrics = score_predictions(general_rows)
    specialist_rate = review_rate(
        specialist_metrics["status_counts"], specialist_metrics["evaluated_items"]
    )
    general_rate = review_rate(general_metrics["status_counts"], general_metrics["evaluated_items"])
    mode = costs["variable_cost_mode"]
    baseline_variable = _variable(costs["baseline"], mode, general_rate)
    specialist_variable = _variable(costs["specialist"], mode, specialist_rate)
    baseline_fixed = money(costs["baseline"]["fixed_cost"])
    specialist_fixed = money(costs["specialist"]["fixed_cost"])
    crossover = solve_crossover(
        baseline_fixed=baseline_fixed,
        baseline_variable=baseline_variable,
        specialist_fixed=specialist_fixed,
        specialist_variable=specialist_variable,
    )
    quality = _quality_gate(costs["quality_gate"], specialist_metrics)
    recommendation = _recommendation(quality, crossover, costs["forecast_volume"])
    sensitivity = _sensitivity(
        costs,
        specialist_rate,
        general_rate,
        quality["specialist_macro_f1"],
    )
    support = {label: 0 for label in LABELS}
    for row in evaluation_items:
        support[row["label"]] += 1
    return {
        "schema_version": "1.0.0",
        "task_id": dataset["task_id"],
        "profile_id": costs["profile_id"],
        "currency": costs["currency"],
        "horizon": costs["horizon"],
        "forecast_volume": costs["forecast_volume"],
        "variable_cost_mode": mode,
        "quality_gate": quality,
        "recommendation": recommendation,
        "models": {
            "general": {
                "name": trace["model"]["name"],
                "revision": trace["model"]["revision"],
                "provider": trace["model"]["provider"],
                "provenance": "recorded",
                "metrics": _public(general_metrics),
                "review_rate": format(general_rate, "f"),
                "wall_time_ms_total": trace["run"]["wall_time_ms_total"],
                "hardware": trace["model"]["hardware"],
            },
            "specialist": {
                "name": "tfidf-logistic-regression",
                "revision": f"seed-{model['seed']}",
                "provenance": "trained-this-run",
                "threshold": model["threshold"],
                "threshold_source": "validation macro-F1, ties take the lower threshold",
                "validation_macro_f1": model["validation_metrics"]["macro_f1"],
                "metrics": _public(specialist_metrics),
                "review_rate": format(specialist_rate, "f"),
                "train_wall_time_ms": model["train_wall_time_ms"],
                "evaluation_wall_time_ms": eval_ms,
                "train_items": model["train_items"],
                "validation_items": model["validation_items"],
            },
        },
        "costs": {
            "provenance": "analyst-supplied",
            "note": "Dollar amounts are the cost profile. Wall times above are recorded and are not converted to money.",
            "baseline": _party_view(costs["baseline"], baseline_variable, general_rate),
            "specialist": _party_view(costs["specialist"], specialist_variable, specialist_rate),
            "crossover": crossover,
        },
        "sensitivity": sensitivity,
        "support": support,
        "example": _example(combined),
        "items": combined,
        "timings": {
            "provenance": "recorded",
            "general_trace_wall_time_ms_total": trace["run"]["wall_time_ms_total"],
            "general_trace_host": trace["run"]["host"],
            "specialist_train_wall_time_ms": model["train_wall_time_ms"],
            "specialist_evaluation_wall_time_ms": eval_ms,
            "analysis_host": f"{platform.system()} {platform.machine()} {platform.python_version()}",
        },
        "limitations": [
            "One four-label synthetic task. Results do not transfer to other label sets.",
            "The general model is the pinned lexical-generalist trace, not a hosted LLM.",
            "Cost dollars are analyst-supplied assumptions for the stated horizon.",
            "A passing quality gate is required before the specialist is marked eligible.",
            "The linear export is for inspection. This run retrained the specialist and did not load it.",
        ],
        "specialist_export": model["export"],
    }


def _variable(party: dict[str, Any], mode: str, observed_rate: Decimal) -> Decimal:
    if mode == "modeled":
        return money(party["modeled_variable_cost_per_request"])
    return money(party["inference_cost_per_request"]) + observed_rate * money(
        party["review_cost_per_item"]
    )


def _quality_gate(gate: dict[str, str], metrics: dict[str, Any]) -> dict[str, Any]:
    minimum_f1 = money(gate["min_macro_f1"])
    minimum_recall = money(gate["min_per_class_recall"])
    passed = (
        metrics["macro_f1_exact"] >= minimum_f1 and metrics["min_recall_exact"] >= minimum_recall
    )
    return {
        "min_macro_f1": gate["min_macro_f1"],
        "min_per_class_recall": gate["min_per_class_recall"],
        "specialist_macro_f1": metrics["macro_f1"],
        "specialist_min_recall": metrics["min_recall"],
        "passed": passed,
    }


def _recommendation(
    quality: dict[str, Any], crossover: dict[str, Any], forecast: int
) -> dict[str, Any]:
    if not quality["passed"]:
        return {
            "eligible": False,
            "scenario_shown": True,
            "reason": (
                "The specialist missed the quality gate. Cost arithmetic is still reported "
                "and no eligible recommendation is made."
            ),
        }
    outcome = crossover["outcome"]
    if outcome == "already_cheaper":
        return {
            "eligible": True,
            "scenario_shown": True,
            "reason": "Quality passed and the specialist is already cheaper at every positive volume.",
        }
    if outcome == "finite_crossover":
        first = crossover["first_strict_saving_request"]
        if forecast >= first:
            return {
                "eligible": True,
                "scenario_shown": True,
                "reason": (
                    f"Quality passed. Forecast volume {forecast} is at or beyond the first "
                    f"strict saving at request {first}."
                ),
            }
        return {
            "eligible": False,
            "scenario_shown": True,
            "reason": (
                f"Quality passed, but forecast volume {forecast} is before the first strict "
                f"saving at request {first}."
            ),
        }
    return {
        "eligible": False,
        "scenario_shown": True,
        "reason": crossover["reason"],
    }


def _sensitivity(
    costs: dict[str, Any],
    specialist_rate: Decimal,
    general_rate: Decimal,
    frozen_macro_f1: str,
) -> list[dict[str, Any]]:
    rows = []
    for review_cost in costs["sensitivity_review_costs"]:
        price = money(review_cost)
        baseline_variable = (
            money(costs["baseline"]["inference_cost_per_request"]) + general_rate * price
        )
        specialist_variable = (
            money(costs["specialist"]["inference_cost_per_request"]) + specialist_rate * price
        )
        crossover = solve_crossover(
            baseline_fixed=money(costs["baseline"]["fixed_cost"]),
            baseline_variable=baseline_variable,
            specialist_fixed=money(costs["specialist"]["fixed_cost"]),
            specialist_variable=specialist_variable,
        )
        rows.append(
            {
                "review_cost_per_item": format(price, "f"),
                "provenance": "analyst-supplied review price; observed review rates; quality frozen",
                "frozen_specialist_macro_f1": frozen_macro_f1,
                "baseline_review_rate": format(general_rate, "f"),
                "specialist_review_rate": format(specialist_rate, "f"),
                "baseline_variable_cost_per_request": format(baseline_variable, "f"),
                "specialist_variable_cost_per_request": format(specialist_variable, "f"),
                "crossover": crossover,
            }
        )
    return rows


def _party_view(party: dict[str, Any], variable: Decimal, rate: Decimal) -> dict[str, Any]:
    return {
        "fixed_cost": party["fixed_cost"],
        "components": party["components"],
        "inference_cost_per_request": party["inference_cost_per_request"],
        "review_cost_per_item": party["review_cost_per_item"],
        "observed_review_rate": format(rate, "f"),
        "variable_cost_per_request": format(variable, "f"),
        "modeled_variable_cost_per_request": party["modeled_variable_cost_per_request"],
        "provenance": party["provenance"],
    }


def _example(items: list[dict[str, Any]]) -> dict[str, Any]:
    chosen = next(
        (item for item in items if item["template_family"] == "hvac-condensate-leak"),
        items[0],
    )
    return {
        "item_id": chosen["item_id"],
        "template_family": chosen["template_family"],
        "text": chosen["text"],
        "gold": chosen["gold"],
        "specialist_label": chosen["specialist_label"],
        "specialist_status": chosen["specialist_status"],
        "general_label": chosen["general_label"],
        "general_status": chosen["general_status"],
        "how_to_trace": "Find this item_id in the dataset file recorded under inputs.dataset.",
    }


def _public(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if not key.endswith("_exact")}
