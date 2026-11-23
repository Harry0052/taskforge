"""Write the machine-readable report and a short human summary from one result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taskforge.errors import TaskForgeError


def write_report(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Write only inside `output_dir`. Returns the file paths."""
    if output_dir.exists() and not output_dir.is_dir():
        raise TaskForgeError(
            "output_path",
            f"{output_dir} exists and is not a directory. Choose a directory for the report.",
        )
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise TaskForgeError(
            "output_path",
            f"could not create output directory {output_dir}: {exc}",
        ) from exc
    resolved = output_dir.resolve()
    report_json = _inside(resolved, "report.json")
    report_md = _inside(resolved, "report.md")
    export_path = _inside(resolved, "specialist-export.json")
    export = result["specialist_export"]
    public = {key: value for key, value in result.items() if key != "specialist_export"}
    report_json.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    export_path.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(render_markdown(public), encoding="utf-8")
    return {
        "report_json": str(report_json),
        "report_md": str(report_md),
        "specialist_export": str(export_path),
    }


def render_markdown(result: dict[str, Any]) -> str:
    specialist = result["models"]["specialist"]
    general = result["models"]["general"]
    gate = result["quality_gate"]
    crossover = result["costs"]["crossover"]
    recommendation = result["recommendation"]
    lines = [
        "# TaskForge report",
        "",
        f"Task `{result['task_id']}`, profile `{result['profile_id']}`.",
        f"Currency {result['currency']}. Horizon: {result['horizon']}. "
        f"Forecast volume: {result['forecast_volume']} requests.",
        "",
        "## Decision",
        "",
        f"Eligible recommendation: **{recommendation['eligible']}**.",
        "",
        recommendation["reason"],
        "",
        f"Quality gate passed: {gate['passed']} "
        f"(specialist macro-F1 {gate['specialist_macro_f1']}, "
        f"minimum per-class recall {gate['specialist_min_recall']}; "
        f"required macro-F1 {gate['min_macro_f1']} and recall {gate['min_per_class_recall']}).",
        "",
        f"Cost outcome: `{crossover['outcome']}`. {crossover['reason']}",
        "",
        "## Quality",
        "",
        "Recorded on the locked evaluation ids. Support includes abstentions, timeouts, and no-results.",
        "",
        "| Label | Support | Specialist recall | General recall |",
        "| --- | ---: | ---: | ---: |",
    ]
    general_by_label = {row["label"]: row for row in general["metrics"]["per_label"]}
    for row in specialist["metrics"]["per_label"]:
        other = general_by_label[row["label"]]
        lines.append(f"| {row['label']} | {row['support']} | {row['recall']} | {other['recall']} |")
    lines.extend(
        [
            "",
            f"Specialist macro-F1: {specialist['metrics']['macro_f1']}. "
            f"Abstentions {specialist['metrics']['abstentions']}, "
            f"timeouts {specialist['metrics']['timeouts']}, "
            f"no-results {specialist['metrics']['no_results']}.",
            f"General macro-F1: {general['metrics']['macro_f1']}. "
            f"Abstentions {general['metrics']['abstentions']}, "
            f"timeouts {general['metrics']['timeouts']}, "
            f"no-results {general['metrics']['no_results']}.",
            f"Specialist confidence cutoff {specialist['threshold']} was frozen on validation "
            f"(validation macro-F1 {specialist['validation_macro_f1']}).",
            "",
            "## Costs",
            "",
            "Analyst-supplied. These dollars are not derived from the wall times in the next section.",
            "",
            f"Baseline fixed {result['costs']['baseline']['fixed_cost']} "
            f"(labeling {result['costs']['baseline']['components']['labeling']}, "
            f"training {result['costs']['baseline']['components']['training']}, "
            f"integration {result['costs']['baseline']['components']['integration']}). "
            f"Variable per request {result['costs']['baseline']['variable_cost_per_request']}.",
            f"Specialist fixed {result['costs']['specialist']['fixed_cost']} "
            f"(labeling {result['costs']['specialist']['components']['labeling']}, "
            f"training {result['costs']['specialist']['components']['training']}, "
            f"integration {result['costs']['specialist']['components']['integration']}). "
            f"Variable per request {result['costs']['specialist']['variable_cost_per_request']}.",
            f"Variable cost mode: `{result['variable_cost_mode']}`.",
            "",
        ]
    )
    if crossover.get("totals_at_equality"):
        tie = crossover["totals_at_equality"]
        lines.append(
            f"At {tie['requests']} requests the totals are equal: "
            f"baseline {tie['baseline_total']}, specialist {tie['specialist_total']}."
        )
    if crossover.get("totals_at_first_strict_saving"):
        nxt = crossover["totals_at_first_strict_saving"]
        lines.append(
            f"At {nxt['requests']} requests the specialist total is {nxt['specialist_total']} "
            f"and the baseline total is {nxt['baseline_total']} "
            f"(difference {nxt['specialist_minus_baseline']})."
        )
    if result["sensitivity"]:
        lines.extend(
            [
                "",
                "## Review-cost sensitivity",
                "",
                "Quality figures stay at the frozen macro-F1.",
                "",
            ]
        )
        for row in result["sensitivity"]:
            outcome = row["crossover"]["outcome"]
            first = row["crossover"]["first_strict_saving_request"]
            lines.append(
                f"- Review price {row['review_cost_per_item']} ({row['provenance']}): "
                f"outcome `{outcome}`, first strict saving {first}, "
                f"frozen macro-F1 {row['frozen_specialist_macro_f1']}."
            )
    timings = result["timings"]
    example = result["example"]
    lines.extend(
        [
            "",
            "## Recorded timings",
            "",
            f"General-model trace wall time {timings['general_trace_wall_time_ms_total']} ms "
            f"on {timings['general_trace_host']}.",
            f"Specialist training {timings['specialist_train_wall_time_ms']} ms and "
            f"evaluation scoring {timings['specialist_evaluation_wall_time_ms']} ms "
            f"on {timings['analysis_host']}.",
            "These measurements are not prices.",
            "",
            "## Traced example",
            "",
            f"Item `{example['item_id']}` ({example['template_family']}) gold `{example['gold']}`.",
            f"Text: {example['text']}",
            f"Specialist: {example['specialist_status']} / {example['specialist_label']}. "
            f"General model: {example['general_status']} / {example['general_label']}.",
            example["how_to_trace"],
            "",
            "## Limitations",
            "",
        ]
    )
    for note in result["limitations"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _inside(directory: Path, name: str) -> Path:
    path = (directory / name).resolve()
    if path.parent != directory:
        raise ValueError(f"refusing to write outside {directory}")
    return path
