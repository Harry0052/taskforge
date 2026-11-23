"""The public analyze command on the shipped fixture and the failure cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from taskforge.cli import main

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "taskforge" / "data"
DATASET = DATA / "dataset.json"
TRACE = DATA / "general_trace.json"


def test_demo_profile_matches_the_oracle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATASET),
            "--trace",
            str(TRACE),
            "--costs",
            str(DATA / "costs" / "demo.json"),
            "--output",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    summary = json.loads(captured.out)
    assert summary["eligible"] is True
    assert summary["quality_gate_passed"] is True
    assert summary["equality_requests"] == 4000
    assert summary["first_strict_saving_request"] == 4001
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["currency"] == "USD"
    assert report["horizon"] == "12 months"
    assert report["forecast_volume"] == 10000
    assert report["costs"]["provenance"] == "analyst-supplied"
    assert report["timings"]["provenance"] == "recorded"
    support = {
        row["label"]: row["support"]
        for row in report["models"]["specialist"]["metrics"]["per_label"]
    }
    assert support == report["support"]
    assert sum(support.values()) == 22
    general = report["models"]["general"]["metrics"]
    assert general["timeouts"] == 1
    assert general["no_results"] == 1
    assert general["evaluated_items"] == 22
    macro = report["quality_gate"]["specialist_macro_f1"]
    assert len(report["sensitivity"]) == 2
    assert {row["frozen_specialist_macro_f1"] for row in report["sensitivity"]} == {macro}
    first_savings = [
        row["crossover"]["first_strict_saving_request"] for row in report["sensitivity"]
    ]
    assert first_savings[0] != first_savings[1]
    example = report["example"]
    dataset = (DATASET).read_text(encoding="utf-8")
    assert example["item_id"] in dataset
    assert example["text"] in dataset
    export = json.loads((tmp_path / "specialist-export.json").read_text(encoding="utf-8"))
    assert export["format"] == "taskforge-linear-export"
    assert "coef" in export
    raw_export = (tmp_path / "specialist-export.json").read_bytes()
    assert b"pickle" not in raw_export.lower()
    markdown = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Analyst-supplied" in markdown
    assert "Recorded timings" in markdown
    assert "4000" in markdown
    assert "4001" in markdown


def test_unfavorable_profile_has_no_large_volume_break_even(tmp_path: Path) -> None:
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATASET),
            "--trace",
            str(TRACE),
            "--costs",
            str(DATA / "costs" / "unfavorable.json"),
            "--output",
            str(tmp_path),
        ]
    )
    assert code == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["quality_gate"]["passed"] is True
    assert report["recommendation"]["eligible"] is False
    assert report["costs"]["crossover"]["outcome"] == "no_favorable_large_volume_break_even"


def test_low_volume_forecast_is_before_the_saving(tmp_path: Path) -> None:
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATASET),
            "--trace",
            str(TRACE),
            "--costs",
            str(DATA / "costs" / "low_volume.json"),
            "--output",
            str(tmp_path),
        ]
    )
    assert code == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["costs"]["crossover"]["equality_requests"] == 4000
    assert report["recommendation"]["eligible"] is False
    assert "before the first strict saving" in report["recommendation"]["reason"]


def test_failed_quality_gate_keeps_the_arithmetic_and_withholds_eligibility(
    tmp_path: Path,
) -> None:
    profile = json.loads((DATA / "costs" / "demo.json").read_text(encoding="utf-8"))
    profile["quality_gate"]["min_macro_f1"] = "0.9900"
    path = tmp_path / "strict.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    out = tmp_path / "out"
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATASET),
            "--trace",
            str(TRACE),
            "--costs",
            str(path),
            "--output",
            str(out),
        ]
    )
    assert code == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["quality_gate"]["passed"] is False
    assert report["recommendation"]["eligible"] is False
    assert report["costs"]["crossover"]["equality_requests"] == 4000
    assert report["costs"]["crossover"]["first_strict_saving_request"] == 4001


def test_analyze_rejects_a_leaked_family(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATA / "invalid" / "leaked_family.json"),
            "--trace",
            str(TRACE),
            "--costs",
            str(DATA / "costs" / "demo.json"),
            "--output",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.startswith("template_family_leak:")
    assert not (tmp_path / "report.json").exists()
