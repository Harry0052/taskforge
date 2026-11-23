"""Trust-boundary checks: schema versions, money, file size, and output paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from taskforge.cli import main
from taskforge.errors import TaskForgeError
from taskforge.report import write_report
from taskforge.validate import MAX_FILE_BYTES, load_json_object, validate_costs, validate_trace

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "taskforge" / "data"


def _dataset() -> dict:
    return json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))


def test_unknown_trace_schema_is_rejected() -> None:
    trace = json.loads((DATA / "general_trace.json").read_text(encoding="utf-8"))
    trace["schema_version"] = "2.0.0"
    with pytest.raises(TaskForgeError) as caught:
        validate_trace(trace, _dataset())
    assert caught.value.code == "unsupported_schema_version"


def test_trace_label_outside_the_dictionary_is_rejected() -> None:
    trace = json.loads((DATA / "general_trace.json").read_text(encoding="utf-8"))
    trace["results"][0]["output_label"] = "mechanical"
    trace["results"][0]["scoring_status"] = "scored"
    trace["results"][0]["timeout"] = False
    with pytest.raises(TaskForgeError) as caught:
        validate_trace(trace, _dataset())
    assert caught.value.code == "label_dictionary_mismatch"


def test_component_sum_must_match_fixed_cost() -> None:
    profile = json.loads((DATA / "costs" / "demo.json").read_text(encoding="utf-8"))
    profile["specialist"]["components"]["integration"] = "0.0000"
    with pytest.raises(TaskForgeError) as caught:
        validate_costs(profile)
    assert caught.value.code == "money_bounds"
    assert "add up" in caught.value.message


def test_negative_money_is_rejected() -> None:
    profile = json.loads((DATA / "costs" / "demo.json").read_text(encoding="utf-8"))
    profile["baseline"]["modeled_variable_cost_per_request"] = "-0.0100"
    with pytest.raises(TaskForgeError) as caught:
        validate_costs(profile)
    assert caught.value.code == "money_bounds"


def test_oversized_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "big.json"
    path.write_bytes(b"{" + b" " * (MAX_FILE_BYTES + 1))
    with pytest.raises(TaskForgeError) as caught:
        load_json_object(path)
    assert caught.value.code == "input_too_large"


def test_report_writer_refuses_a_file_path(tmp_path: Path) -> None:
    target = tmp_path / "not-a-directory"
    target.write_text("busy", encoding="utf-8")
    with pytest.raises(TaskForgeError) as caught:
        write_report({"specialist_export": {}, "limitations": []}, target)
    assert caught.value.code == "output_path"
    assert target.read_text(encoding="utf-8") == "busy"


def test_analyze_output_path_error_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "blocked"
    target.write_text("busy", encoding="utf-8")
    code = main(
        [
            "analyze",
            "--dataset",
            str(DATA / "dataset.json"),
            "--trace",
            str(DATA / "general_trace.json"),
            "--costs",
            str(DATA / "costs" / "demo.json"),
            "--output",
            str(target),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.startswith("output_path:")
    assert target.read_text(encoding="utf-8") == "busy"
