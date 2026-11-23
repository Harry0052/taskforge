"""Write the synthetic fixtures and the one local generalist trace.

Texts are original sentences for this repository. The seed is recorded in the
manifest. Re-running this script refreshes measured wall times and the host
string, then rewrites checksums. The committed files are the demo inputs.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from taskforge.generalist import MODEL_NAME, MODEL_REVISION, record_trace  # noqa: E402

SEED = 17001
SCHEMA = "1.0.0"
TASK_ID = "facilities-work-order-routing"
DATA = SRC / "taskforge" / "data"

# split, label, family, texts. Paraphrases of one family stay in one split.
FAMILIES: list[tuple[str, str, str, list[str]]] = [
    (
        "train",
        "hvac",
        "hvac-east-thermostat",
        [
            "The east wing thermostat will not hold the afternoon setpoint.",
            "Setpoint drift on the east wing thermostat leaves the offices warm.",
            "East wing rooms miss the thermostat setpoint after lunch.",
        ],
    ),
    (
        "train",
        "hvac",
        "hvac-roof-condenser",
        [
            "The roof condenser short-cycles all afternoon.",
            "Short-cycling condenser on the roof starts every few minutes.",
            "Roof condenser ice rings the coil and then clears.",
        ],
    ),
    (
        "train",
        "hvac",
        "hvac-floor-duct",
        [
            "Supply duct airflow is weak on the second floor.",
            "Second floor supply duct has almost no airflow at the diffusers.",
            "Airflow in the second floor supply duct barely moves a tissue.",
        ],
    ),
    (
        "train",
        "hvac",
        "hvac-handler-condensate",
        [
            "The mezzanine air handler condensate pan is full.",
            "Air handler condensate pan on the mezzanine needs emptying.",
            "Condensate from the mezzanine air handler is at the pan rim.",
        ],
    ),
    (
        "validation",
        "hvac",
        "hvac-lobby-airflow",
        [
            "Lobby airflow drops whenever the afternoon sun hits the glass.",
            "Afternoon lobby airflow never recovers after the doors cycle.",
        ],
    ),
    (
        "validation",
        "hvac",
        "hvac-suite-filter",
        [
            "The suite filter bank is loaded and the rooms stay stale.",
            "A loaded filter bank is starving the suite of supply air.",
        ],
    ),
    (
        "evaluation",
        "hvac",
        "hvac-lab-condenser",
        [
            "The lab condenser is iced over and the coil is blocked.",
            "Ice on the lab condenser is stopping the coil.",
        ],
    ),
    (
        "evaluation",
        "hvac",
        "hvac-clinic-duct",
        [
            "Clinic duct airflow died after lunch.",
            "After lunch the clinic duct has no airflow at the nurses station.",
        ],
    ),
    (
        "evaluation",
        "hvac",
        "hvac-condensate-leak",
        [
            "Condensate leak under the air handler by the east stair.",
            "East stair air handler has a condensate leak on the pad.",
        ],
    ),
    (
        "train",
        "plumbing",
        "plumbing-third-faucet",
        [
            "The third floor faucet will not shut off.",
            "Third floor faucet drips into the basin all night.",
            "Night drip from the third floor faucet soaks the cabinet.",
        ],
    ),
    (
        "train",
        "plumbing",
        "plumbing-kitchen-drain",
        [
            "Kitchen drain is slow and holding water after lunch.",
            "The kitchen drain holds standing water at the prep sink.",
            "Slow kitchen drain after the lunch service.",
        ],
    ),
    (
        "train",
        "plumbing",
        "plumbing-closet-valve",
        [
            "Isolation valve in the janitor closet will not turn.",
            "The closet isolation valve is seized shut.",
            "Janitor closet valve does not close all the way.",
        ],
    ),
    (
        "train",
        "plumbing",
        "plumbing-lobby-toilet",
        [
            "Lobby toilet clogged again this morning.",
            "Morning clog in the lobby toilet will not clear.",
            "Lobby toilet is clogged and will not flush.",
        ],
    ),
    (
        "validation",
        "plumbing",
        "plumbing-sink-pipe",
        [
            "A loose pipe under the break room sink is sweating.",
            "Break room sink pipe joint is wet at the slip nut.",
        ],
    ),
    (
        "validation",
        "plumbing",
        "plumbing-floor-clog",
        [
            "Floor drain clog on level one is backing up.",
            "Level one floor drain is clogged after the rain.",
        ],
    ),
    (
        "evaluation",
        "plumbing",
        "plumbing-dock-valve",
        [
            "The dock sink valve is seized and will not isolate.",
            "Seized valve at the dock sink needs a replacement.",
        ],
    ),
    (
        "evaluation",
        "plumbing",
        "plumbing-hall-toilet",
        [
            "Hall toilet by the conference room is clogged.",
            "Conference hall toilet clogged before the tour.",
        ],
    ),
    (
        "evaluation",
        "plumbing",
        "plumbing-cafe-drain",
        [
            "Cafe drain is holding gray water at the hand sink.",
            "The cafe hand sink drain will not empty.",
        ],
    ),
    (
        "train",
        "electrical",
        "electrical-copy-breaker",
        [
            "Copy room breaker trips when the second printer starts.",
            "The copy room breaker is warm and trips after lunch.",
            "Breaker for the copy room will not stay closed.",
        ],
    ),
    (
        "train",
        "electrical",
        "electrical-garage-ballast",
        [
            "Parking garage ballast buzzes and the lamp flickers.",
            "Garage ballast will not strike the lamp on row C.",
            "Row C ballast in the garage hums and then drops the lamp.",
        ],
    ),
    (
        "train",
        "electrical",
        "electrical-lobby-outlet",
        [
            "Lobby floor outlet has no power for the display.",
            "The lobby outlet is dead on the north wall.",
            "North lobby outlet lost power overnight.",
        ],
    ),
    (
        "train",
        "electrical",
        "electrical-boiler-panel",
        [
            "Electrical panel in the boiler room is warm to the touch.",
            "Boiler room panel door is hot around the main lugs.",
            "The boiler room electrical panel smells warm.",
        ],
    ),
    (
        "validation",
        "electrical",
        "electrical-hall-circuit",
        [
            "Hall circuit for the badge readers keeps opening.",
            "Badge reader circuit in the hall drops twice a morning.",
        ],
    ),
    (
        "validation",
        "electrical",
        "electrical-lamp-voltage",
        [
            "Voltage at the lamp whip in the shop is low.",
            "Shop lamp voltage sags when the compressor starts.",
        ],
    ),
    (
        "evaluation",
        "electrical",
        "electrical-warehouse-ballast",
        [
            "Warehouse ballast will not strike over aisle four.",
            "Aisle four warehouse ballast flickers and then stays dark.",
        ],
    ),
    (
        "evaluation",
        "electrical",
        "electrical-office-outlet",
        [
            "Office outlet behind the plotter has no power.",
            "The plotter outlet in the office is dead.",
        ],
    ),
    (
        "evaluation",
        "electrical",
        "electrical-priority-hold",
        [
            "Copy room breaker is hot and the ticket says priority hold until the vendor calls back.",
        ],
    ),
    (
        "train",
        "custodial",
        "custodial-lobby-trash",
        [
            "Lobby trash cans overflowed before the morning tour.",
            "Morning tour found lobby trash piled beside the cans.",
            "Trash from the lobby event was left at the elevators.",
        ],
    ),
    (
        "train",
        "custodial",
        "custodial-hall-spill",
        [
            "Hall spill by the vending machine needs a mop.",
            "A spill in the east hall is still slick.",
            "East hall spill was reported after the coffee service.",
        ],
    ),
    (
        "train",
        "custodial",
        "custodial-night-wax",
        [
            "Night crew left wax streaks across the lobby stone.",
            "Lobby wax from the night crew is still tacky.",
            "Tacky wax streaks remain on the lobby stone.",
        ],
    ),
    (
        "train",
        "custodial",
        "custodial-dock-recycle",
        [
            "Dock recycle bins were not swapped last night.",
            "Recycle bins at the dock are full and unsorted.",
            "Full recycle bins are blocking the dock pedestrian door.",
        ],
    ),
    (
        "validation",
        "custodial",
        "custodial-restroom-mop",
        [
            "A mop bucket was left in the north restroom.",
            "North restroom still has a mop bucket in the aisle.",
        ],
    ),
    (
        "validation",
        "custodial",
        "custodial-atrium-trash",
        [
            "Atrium trash was not pulled after the reception.",
            "Reception trash is still bagged in the atrium.",
        ],
    ),
    (
        "evaluation",
        "custodial",
        "custodial-atrium-wax",
        [
            "Atrium floor wax is sticky along the main path.",
            "Sticky wax on the atrium floor is catching shoes.",
        ],
    ),
    (
        "evaluation",
        "custodial",
        "custodial-cafe-spill",
        [
            "Cafe spill near the pastry case is still wet.",
            "Wet spill by the cafe pastry case needs a cone.",
        ],
    ),
    (
        "evaluation",
        "custodial",
        "custodial-unreadable",
        [
            "Loading dock spill note is an unreadable attachment from the night crew.",
        ],
    ),
]


def _items() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for split, label, family, texts in FAMILIES:
        for index, text in enumerate(texts, start=1):
            rows.append(
                {
                    "item_id": f"wo-{split[:5]}-{label}-{family.split('-', 1)[1]}-{index:02d}",
                    "text": text,
                    "label": label,
                    "template_family": family,
                    "split": split,
                }
            )
    rows.sort(key=lambda row: row["item_id"])
    return rows


def _party(
    fixed: str,
    labeling: str,
    training: str,
    integration: str,
    inference: str,
    review: str,
    modeled: str | None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "fixed_cost": fixed,
        "components": {
            "labeling": labeling,
            "training": training,
            "integration": integration,
        },
        "inference_cost_per_request": inference,
        "review_cost_per_item": review,
        "provenance": "analyst-supplied",
    }
    if modeled is not None:
        body["modeled_variable_cost_per_request"] = modeled
    return body


def _profile(
    profile_id: str,
    horizon: str,
    volume: int,
    mode: str,
    baseline: dict[str, object],
    specialist: dict[str, object],
    sensitivity: list[str] | None = None,
) -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": SCHEMA,
        "profile_id": profile_id,
        "currency": "USD",
        "horizon": horizon,
        "forecast_volume": volume,
        "variable_cost_mode": mode,
        "baseline": baseline,
        "specialist": specialist,
        "quality_gate": {
            "min_macro_f1": "0.7500",
            "min_per_class_recall": "0.5000",
        },
    }
    if sensitivity is not None:
        document["sensitivity_review_costs"] = sensitivity
    return document


def _costs() -> dict[str, dict[str, object]]:
    gate_base = _party("0.0000", "0.0000", "0.0000", "0.0000", "0.0180", "0.2000", "0.0200")
    gate_spec = _party("60.0000", "40.0000", "5.0000", "15.0000", "0.0030", "0.2000", "0.0050")
    return {
        "demo.json": _profile(
            "demo-modeled",
            "12 months",
            10000,
            "modeled",
            gate_base,
            gate_spec,
            ["0.1000", "0.5000"],
        ),
        "low_volume.json": _profile(
            "low-volume",
            "12 months",
            500,
            "modeled",
            gate_base,
            gate_spec,
        ),
        "high_volume.json": _profile(
            "high-volume",
            "12 months",
            20000,
            "modeled",
            gate_base,
            gate_spec,
        ),
        "high_review.json": _profile(
            "high-review",
            "12 months",
            10000,
            "observed_review",
            _party("0.0000", "0.0000", "0.0000", "0.0000", "0.0100", "2.0000", None),
            _party("60.0000", "40.0000", "5.0000", "15.0000", "0.0020", "2.0000", None),
        ),
        "unfavorable.json": _profile(
            "unfavorable-both-higher",
            "12 months",
            100000,
            "modeled",
            _party("10.0000", "0.0000", "0.0000", "10.0000", "0.0150", "0.1000", "0.0200"),
            _party("90.0000", "50.0000", "10.0000", "30.0000", "0.0200", "0.1000", "0.0300"),
        ),
    }


def _invalid(items: list[dict[str, str]]) -> None:
    invalid = DATA / "invalid"
    invalid.mkdir(parents=True, exist_ok=True)
    repeated = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "plumbing"],
        "items": [
            {**items[0]},
            {**items[0], "text": "Repeated id should be rejected before scoring."},
        ],
    }
    leaked = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "plumbing"],
        "items": [
            {
                "item_id": "wo-leak-train-01",
                "text": "Train paraphrase of a shared family.",
                "label": "hvac",
                "template_family": "hvac-shared-family",
                "split": "train",
            },
            {
                "item_id": "wo-leak-val-01",
                "text": "Validation row so the split set is complete.",
                "label": "plumbing",
                "template_family": "plumbing-val-only",
                "split": "validation",
            },
            {
                "item_id": "wo-leak-eval-01",
                "text": "Evaluation paraphrase of the same family as train.",
                "label": "hvac",
                "template_family": "hvac-shared-family",
                "split": "evaluation",
            },
        ],
    }
    mixed = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "mechanical"],
        "items": [
            {
                "item_id": "wo-mixed-01",
                "text": "A label dictionary that is not the task dictionary.",
                "label": "mechanical",
                "template_family": "mechanical-one",
                "split": "train",
            }
        ],
    }
    bad_schema = {"schema_version": "9.9.9", "task_id": TASK_ID}
    long_text = "x" * 2001
    oversized = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "plumbing"],
        "items": [
            {
                "item_id": "wo-big-train-01",
                "text": "Short train row.",
                "label": "hvac",
                "template_family": "hvac-big-train",
                "split": "train",
            },
            {
                "item_id": "wo-big-val-01",
                "text": "Short validation row.",
                "label": "plumbing",
                "template_family": "plumbing-big-val",
                "split": "validation",
            },
            {
                "item_id": "wo-big-eval-01",
                "text": long_text,
                "label": "electrical",
                "template_family": "electrical-big-eval",
                "split": "evaluation",
            },
        ],
    }
    float_money = _profile(
        "float-money",
        "12 months",
        10,
        "modeled",
        _party("0.0000", "0.0000", "0.0000", "0.0000", "0.0100", "0.1000", "0.0200"),
        _party("60.0000", "40.0000", "5.0000", "15.0000", "0.0030", "0.1000", "0.0050"),
    )
    float_money["specialist"]["modeled_variable_cost_per_request"] = 0.005  # type: ignore[index]
    tiny_items = [
        {
            "item_id": "wo-miss-train-01",
            "text": "Train row for the missing-trace fixture.",
            "label": "hvac",
            "template_family": "hvac-miss-train",
            "split": "train",
        },
        {
            "item_id": "wo-miss-val-01",
            "text": "Validation row for the missing-trace fixture.",
            "label": "plumbing",
            "template_family": "plumbing-miss-val",
            "split": "validation",
        },
        {
            "item_id": "wo-miss-eval-01",
            "text": "First evaluation row, present in the trace.",
            "label": "electrical",
            "template_family": "electrical-miss-a",
            "split": "evaluation",
        },
        {
            "item_id": "wo-miss-eval-02",
            "text": "Second evaluation row, omitted from the trace.",
            "label": "custodial",
            "template_family": "custodial-miss-b",
            "split": "evaluation",
        },
    ]
    missing_dataset = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "plumbing"],
        "items": tiny_items,
    }
    missing_trace = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "model": {
            "name": "lexical-generalist",
            "revision": "1.0.0",
            "provider": "local",
            "hardware": "fixture",
        },
        "run": {
            "seed": SEED,
            "started_at": "2026-11-23T00:00:00+00:00",
            "host": "fixture",
            "wall_time_ms_total": 0.1,
            "randomness": "none",
        },
        "results": [
            {
                "item_id": "wo-miss-eval-01",
                "output_label": "electrical",
                "timeout": False,
                "scoring_status": "scored",
                "wall_time_ms": 0.1,
                "confidence": 1.0,
            }
        ],
    }
    _dump(invalid / "repeated_ids.json", repeated)
    _dump(invalid / "leaked_family.json", leaked)
    _dump(invalid / "mixed_labels.json", mixed)
    _dump(invalid / "bad_schema.json", bad_schema)
    _dump(invalid / "oversized_text.json", oversized)
    _dump(invalid / "float_money.json", float_money)
    _dump(invalid / "missing_general_dataset.json", missing_dataset)
    _dump(invalid / "missing_general_trace.json", missing_trace)


def _dump(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    items = _items()
    dataset = {
        "schema_version": SCHEMA,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA,
        "label_set": ["custodial", "electrical", "hvac", "plumbing"],
        "items": items,
    }
    _dump(DATA / "dataset.json", dataset)
    evaluation = [item for item in items if item["split"] == "evaluation"]
    host = f"{platform.system()} {platform.machine()} {platform.python_version()}"
    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    trace = record_trace(
        evaluation,
        task_id=TASK_ID,
        task_schema_version=SCHEMA,
        schema_version=SCHEMA,
        seed=SEED,
        host=host,
        started_at=started_at,
    )
    _dump(DATA / "general_trace.json", trace)
    costs = DATA / "costs"
    for name, document in _costs().items():
        _dump(costs / name, document)
    _invalid(items)
    status_counts: dict[str, int] = {}
    matches = 0
    gold = {item["item_id"]: item["label"] for item in evaluation}
    for row in trace["results"]:
        status_counts[row["scoring_status"]] = status_counts.get(row["scoring_status"], 0) + 1
        if row["scoring_status"] == "scored" and row["output_label"] == gold[row["item_id"]]:
            matches += 1
    manifest_files: list[dict[str, object]] = []
    for path in sorted(DATA.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(ROOT).as_posix()
        manifest_files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {
        "schema_version": SCHEMA,
        "title": "TaskForge synthetic facilities fixtures",
        "license": "MIT",
        "terms": (
            "Original synthetic work orders and cost profiles written for TaskForge. "
            "No third-party corpus, personal data, or model weights are included. "
            "The general-model trace is the output of one local run of lexical-generalist "
            "revision 1.0.0 and may be redistributed with this MIT repository."
        ),
        "generator": "scripts/generate_fixtures.py",
        "seed": SEED,
        "generalist": {"name": MODEL_NAME, "revision": MODEL_REVISION, "provider": "local"},
        "recording": {
            "started_at": started_at,
            "host": host,
            "evaluation_items": len(evaluation),
            "status_counts": status_counts,
            "scored_label_matches": matches,
            "wall_time_ms_total": trace["run"]["wall_time_ms_total"],
        },
        "files": manifest_files,
    }
    _dump(DATA / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "items": len(items),
                "evaluation": len(evaluation),
                "recording": manifest["recording"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
