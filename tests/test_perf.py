"""Demo budget. The bound is wall time on a CPU, not a cost figure."""

from __future__ import annotations

import time
from pathlib import Path

from taskforge.cli import main

BUDGET_SECONDS = 15.0


def test_demo_finishes_within_budget(tmp_path: Path) -> None:
    started = time.perf_counter()
    code = main(["demo", "--output", str(tmp_path)])
    elapsed = time.perf_counter() - started
    assert code == 0
    assert elapsed < BUDGET_SECONDS
    assert (tmp_path / "report.json").is_file()
