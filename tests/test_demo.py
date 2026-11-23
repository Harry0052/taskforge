"""User-facing demo: shipped sample, readable failure, separate stdout and stderr."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from taskforge.cli import main

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "taskforge" / "data"


def test_demo_writes_a_traceable_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["demo", "--output", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    summary = json.loads(captured.out)
    assert summary["status"] == "demo-complete"
    assert summary["equality_requests"] == 4000
    assert summary["first_strict_saving_request"] == 4001
    assert summary["eligible"] is True
    assert summary["currency"] == "USD"
    assert str(tmp_path / "report.md") in captured.err
    assert "Human report:" in captured.err
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "report.md").read_text(encoding="utf-8")
    example = report["example"]["item_id"]
    assert example in (DATA / "dataset.json").read_text(encoding="utf-8")
    assert example in markdown
    assert "Analyst-supplied" in markdown
    assert "Recorded timings" in markdown
    assert (tmp_path / "specialist-export.json").is_file()


def test_demo_malformed_dataset_explains_the_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "demo",
            "--dataset",
            str(DATA / "invalid" / "leaked_family.json"),
            "--output",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "template_family_leak:" in captured.err
    assert "one split" in captured.err
    assert not (tmp_path / "report.json").exists()


def test_demo_partial_trace_names_the_missing_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "demo",
            "--dataset",
            str(DATA / "invalid" / "missing_general_dataset.json"),
            "--trace",
            str(DATA / "invalid" / "missing_general_trace.json"),
            "--output",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert "missing_general_result:" in captured.err
    assert "wo-miss-eval-02" in captured.err
    assert not (tmp_path / "report.json").exists()


def test_help_lists_demo() -> None:
    with pytest.raises(SystemExit) as caught:
        main(["demo", "--help"])
    assert caught.value.code == 0
