"""Command line entry point.

Machine-readable results go to stdout. Errors and help diagnostics go to stderr
when they describe a rejected input. argparse writes help to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from taskforge.errors import TaskForgeError
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
    except TaskForgeError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 2
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
