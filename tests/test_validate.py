"""Fixture validation: the valid bundle is accepted and bad bundles name the problem."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from taskforge.cli import main
from taskforge.errors import TaskForgeError
from taskforge.validate import load_json_object, validate_costs, validate_dataset, validate_paths

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "taskforge" / "data"


def test_valid_fixture_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "validate",
            "--dataset",
            str(DATA / "dataset.json"),
            "--trace",
            str(DATA / "general_trace.json"),
            "--costs",
            str(DATA / "costs" / "demo.json"),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    summary = json.loads(captured.out)
    assert summary["status"] == "valid"
    assert summary["dataset_items"] == 86
    assert summary["trace_results"] == 22
    assert summary["cost_profile"] == "demo-modeled"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("args", "code_name"),
    [
        (["--dataset", str(DATA / "invalid" / "repeated_ids.json")], "duplicate_id"),
        (["--dataset", str(DATA / "invalid" / "leaked_family.json")], "template_family_leak"),
        (["--dataset", str(DATA / "invalid" / "mixed_labels.json")], "label_dictionary_mismatch"),
        (["--dataset", str(DATA / "invalid" / "bad_schema.json")], "unsupported_schema_version"),
        (["--dataset", str(DATA / "invalid" / "oversized_text.json")], "input_too_large"),
        (
            [
                "--dataset",
                str(DATA / "invalid" / "missing_general_dataset.json"),
                "--trace",
                str(DATA / "invalid" / "missing_general_trace.json"),
            ],
            "missing_general_result",
        ),
        (
            [
                "--dataset",
                str(DATA / "dataset.json"),
                "--costs",
                str(DATA / "invalid" / "float_money.json"),
            ],
            "money_type",
        ),
    ],
)
def test_invalid_fixture_is_actionable(
    args: list[str], code_name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["validate", *args])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err.startswith(f"{code_name}:")
    assert len(captured.err.strip()) > len(code_name) + 2


def test_manifest_checksums_match_files() -> None:
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 17001
    assert manifest["license"] == "MIT"
    assert "Original synthetic" in manifest["terms"]
    seen: set[str] = set()
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"]
        assert path.stat().st_size == entry["bytes"]
        seen.add(entry["path"])
    assert "src/taskforge/data/dataset.json" in seen
    assert "src/taskforge/data/general_trace.json" in seen


def test_cost_profiles_and_trace_contract() -> None:
    dataset = validate_dataset(json.loads((DATA / "dataset.json").read_text(encoding="utf-8")))
    families: dict[str, str] = {}
    ids: set[str] = set()
    for item in dataset["items"]:
        assert item["item_id"] not in ids
        ids.add(item["item_id"])
        assert families.setdefault(item["template_family"], item["split"]) == item["split"]
    for name in (
        "demo.json",
        "low_volume.json",
        "high_volume.json",
        "high_review.json",
        "unfavorable.json",
    ):
        profile = validate_costs(json.loads((DATA / "costs" / name).read_text(encoding="utf-8")))
        assert profile["currency"] == "USD"
    summary = validate_paths(DATA / "dataset.json", DATA / "general_trace.json")
    assert summary["model"]["revision"] == "1.0.0"


def test_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "dup.json"
    path.write_text('{"schema_version": "1.0.0", "schema_version": "1.0.0"}\n', encoding="utf-8")
    with pytest.raises(TaskForgeError) as caught:
        load_json_object(path)
    assert caught.value.code == "duplicate_key"


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0


def test_toolchain_imports() -> None:
    import numpy
    import sklearn

    assert numpy.__version__ == "2.2.6"
    assert sklearn.__version__ == "1.9.1"
    assert pytest.__version__ == "9.2.0"
