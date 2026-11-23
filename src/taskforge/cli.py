"""Command line entry point.

Machine-readable results go to stdout. Rejected inputs are explained on stderr.
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
import json
import sys
from pathlib import Path

from taskforge.analyze import analyze_paths
from taskforge.errors import TaskForgeError
from taskforge.report import write_report
from taskforge.validate import validate_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taskforge",
        description=(
            "Compare a CPU specialist with a pinned general model on one "
            "four-label facilities routing task."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser(
        "validate",
        help="Accept a dataset and optional trace or cost profile, or reject it with a code",
    )
    validate.add_argument("--dataset", required=True, type=Path, help="Work-order dataset JSON")
    validate.add_argument("--trace", type=Path, help="Pinned general-model trace JSON")
    validate.add_argument("--costs", type=Path, help="Cost profile JSON")
    analyze = sub.add_parser(
        "analyze",
        help="Train the specialist, score the locked evaluation ids, and write a cost report",
    )
    analyze.add_argument("--dataset", required=True, type=Path)
    analyze.add_argument("--trace", required=True, type=Path)
    analyze.add_argument("--costs", required=True, type=Path)
    analyze.add_argument(
        "--output", required=True, type=Path, help="Directory for report.json and report.md"
    )
    demo = sub.add_parser(
        "demo",
        help="Train on the shipped sample, align the frozen general-model trace, and write a report",
    )
    demo.add_argument("--dataset", type=Path, help="Defaults to the shipped synthetic work orders")
    demo.add_argument(
        "--trace", type=Path, help="Defaults to the recorded lexical-generalist trace"
    )
    demo.add_argument(
        "--costs", type=Path, help="Defaults to the modeled 60 / 0.020 / 0.005 profile"
    )
    demo.add_argument(
        "--output",
        type=Path,
        default=Path("reports/demo"),
        help="Directory for report.json and report.md (default: reports/demo)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            summary = validate_paths(args.dataset, args.trace, args.costs)
            json.dump(summary, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        if args.command == "analyze":
            result = analyze_paths(args.dataset, args.trace, args.costs)
            paths = write_report(result, args.output)
            crossover = result["costs"]["crossover"]
            summary = {
                "status": "analyzed",
                "report": paths["report_json"],
                "summary": paths["report_md"],
                "eligible": result["recommendation"]["eligible"],
                "quality_gate_passed": result["quality_gate"]["passed"],
                "specialist_macro_f1": result["quality_gate"]["specialist_macro_f1"],
                "outcome": crossover["outcome"],
                "equality_requests": crossover["equality_requests"],
                "first_strict_saving_request": crossover["first_strict_saving_request"],
            }
            json.dump(summary, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        if args.command == "demo":
            data = Path(__file__).resolve().parent / "data"
            dataset = args.dataset or data / "dataset.json"
            trace = args.trace or data / "general_trace.json"
            costs = args.costs or data / "costs" / "demo.json"
            result = analyze_paths(dataset, trace, costs)
            paths = write_report(result, args.output)
            crossover = result["costs"]["crossover"]
            summary = {
                "status": "demo-complete",
                "report": paths["report_json"],
                "summary": paths["report_md"],
                "eligible": result["recommendation"]["eligible"],
                "quality_gate_passed": result["quality_gate"]["passed"],
                "specialist_macro_f1": result["quality_gate"]["specialist_macro_f1"],
                "outcome": crossover["outcome"],
                "equality_requests": crossover["equality_requests"],
                "first_strict_saving_request": crossover["first_strict_saving_request"],
                "currency": result["currency"],
                "horizon": result["horizon"],
                "forecast_volume": result["forecast_volume"],
            }
            print(f"Human report: {paths['report_md']}", file=sys.stderr)
            json.dump(summary, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0
    except TaskForgeError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 2
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
