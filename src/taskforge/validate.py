"""Validate versioned dataset, trace, and cost-profile documents.

The validator reads bounded JSON only. It does not train a model and it does
not interpret numbers that were written as JSON floats for money.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from taskforge.errors import TaskForgeError

SCHEMA_VERSION = "1.0.0"
TASK_ID = "facilities-work-order-routing"
LABELS: tuple[str, ...] = ("custodial", "electrical", "hvac", "plumbing")
SPLITS: tuple[str, ...] = ("train", "validation", "evaluation")
SCORING_STATUSES: tuple[str, ...] = ("scored", "abstain", "timeout", "no_result")
VARIABLE_MODES: tuple[str, ...] = ("modeled", "observed_review")
PROVENANCE: tuple[str, ...] = ("analyst-supplied", "recorded")
CURRENCIES: tuple[str, ...] = ("USD",)

MAX_FILE_BYTES = 1_500_000
MAX_ITEMS = 5_000
MAX_TEXT_CHARS = 2_000
MAX_ID_LENGTH = 64
MAX_HORIZON_CHARS = 80
MAX_FORECAST = 10**12
MAX_MONEY = Decimal("1000000000")
MONEY_PLACES = 4

_ID_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")


def load_json_object(path: Path) -> dict[str, Any]:
    """Read one UTF-8 JSON object, rejecting oversized or malformed files."""
    if not path.is_file():
        raise TaskForgeError("missing_file", f"file not found: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise TaskForgeError(
            "input_too_large",
            f"{path} is {len(raw)} bytes; the limit is {MAX_FILE_BYTES} bytes",
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskForgeError(
            "malformed_input",
            f"{path} is not UTF-8 ({exc.reason} at byte {exc.start})",
        ) from exc
    try:
        data = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise TaskForgeError(
            "malformed_input",
            f"{path} is not valid JSON at line {exc.lineno}: {exc.msg}",
        ) from exc
    if not isinstance(data, dict):
        raise TaskForgeError(
            "malformed_input",
            f"{path} must contain a JSON object, not {type(data).__name__}",
        )
    return data


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise TaskForgeError(
                "duplicate_key",
                f"JSON object repeats key '{key}'. Keep each field once.",
            )
        seen[key] = value
    return seen


def _require_keys(
    obj: dict[str, Any], required: tuple[str, ...], where: str, optional: tuple[str, ...] = ()
) -> None:
    allowed = set(required) | set(optional)
    missing = [key for key in required if key not in obj]
    extra = [key for key in obj if key not in allowed]
    if missing or extra:
        raise TaskForgeError(
            "malformed_input",
            f"{where} has missing keys {missing} and unexpected keys {extra}. "
            f"Expected {list(required)}.",
        )


def _require_version(document: dict[str, Any], where: str) -> None:
    version = document.get("schema_version")
    if version != SCHEMA_VERSION:
        raise TaskForgeError(
            "unsupported_schema_version",
            f"{where} schema_version {version!r} is not supported. Use {SCHEMA_VERSION}.",
        )


def _identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_ID_LENGTH:
        raise TaskForgeError(
            "malformed_input",
            f"{where} must be a 1..{MAX_ID_LENGTH} character id of lowercase letters, digits, and hyphens",
        )
    if value[0] == "-" or any(char not in _ID_CHARS for char in value):
        raise TaskForgeError(
            "malformed_input",
            f"{where} id {value!r} must match lowercase letters, digits, and interior hyphens",
        )
    return value


def _string(value: Any, where: str, *, max_chars: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaskForgeError("malformed_input", f"{where} must be a non-empty string")
    if len(value) > max_chars:
        raise TaskForgeError(
            "input_too_large",
            f"{where} is {len(value)} characters; the limit is {max_chars}",
        )
    return value


def parse_money(value: Any, where: str) -> Decimal:
    """Parse a non-negative money amount written as a decimal string."""
    if isinstance(value, bool) or isinstance(value, (int, float)):
        raise TaskForgeError(
            "money_type",
            f"{where} must be a decimal string such as '0.0200', not a JSON number. "
            "JSON numbers are binary and are rejected so totals stay exact.",
        )
    if not isinstance(value, str):
        raise TaskForgeError("money_type", f"{where} must be a decimal string")
    if not value or any(char in value for char in "eE+") or value.count(".") > 1:
        raise TaskForgeError(
            "money_type",
            f"{where} value {value!r} is not a plain non-negative decimal string",
        )
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise TaskForgeError(
            "money_type",
            f"{where} value {value!r} is not a decimal",
        ) from exc
    if amount < 0 or amount > MAX_MONEY:
        raise TaskForgeError(
            "money_bounds",
            f"{where} value {value} is outside 0..{MAX_MONEY}",
        )
    exponent = amount.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -MONEY_PLACES:
        raise TaskForgeError(
            "money_type",
            f"{where} uses more than {MONEY_PLACES} decimal places ({value})",
        )
    return amount.quantize(Decimal("0.0001"))


def parse_unit_interval(value: Any, where: str) -> Decimal:
    amount = parse_money(value, where)
    if amount > 1:
        raise TaskForgeError(
            "money_bounds",
            f"{where} value {value} is outside 0..1",
        )
    return amount


def validate_dataset(document: dict[str, Any]) -> dict[str, Any]:
    """Validate a work-order dataset and return a normalized copy."""
    _require_version(document, "dataset")
    _require_keys(
        document,
        ("schema_version", "task_id", "task_schema_version", "label_set", "items"),
        "dataset",
    )
    if document["task_id"] != TASK_ID:
        raise TaskForgeError(
            "unsupported_task",
            f"task_id {document['task_id']!r} is not {TASK_ID}",
        )
    if document["task_schema_version"] != SCHEMA_VERSION:
        raise TaskForgeError(
            "unsupported_schema_version",
            f"task_schema_version {document['task_schema_version']!r} is not supported. "
            f"Use {SCHEMA_VERSION}.",
        )
    labels = document["label_set"]
    if labels != list(LABELS):
        raise TaskForgeError(
            "label_dictionary_mismatch",
            f"label_set {labels!r} must be exactly {list(LABELS)}",
        )
    items = document["items"]
    if not isinstance(items, list):
        raise TaskForgeError("malformed_input", "dataset.items must be a list")
    if not items or len(items) > MAX_ITEMS:
        raise TaskForgeError(
            "input_too_large" if items else "malformed_input",
            f"dataset.items has {len(items)} rows; allowed range is 1..{MAX_ITEMS}",
        )
    seen_ids: set[str] = set()
    families: dict[str, str] = {}
    split_counts = {split: 0 for split in SPLITS}
    normalized_items: list[dict[str, str]] = []
    for index, item in enumerate(items):
        where = f"items[{index}]"
        if not isinstance(item, dict):
            raise TaskForgeError("malformed_input", f"{where} must be an object")
        _require_keys(
            item,
            ("item_id", "text", "label", "template_family", "split"),
            where,
        )
        item_id = _identifier(item["item_id"], f"{where}.item_id")
        if item_id in seen_ids:
            raise TaskForgeError(
                "duplicate_id",
                f"item_id '{item_id}' is repeated. Give every request one stable id.",
            )
        seen_ids.add(item_id)
        text = _string(item["text"], f"{where}.text ({item_id})", max_chars=MAX_TEXT_CHARS)
        label = item["label"]
        if label not in LABELS:
            raise TaskForgeError(
                "label_dictionary_mismatch",
                f"{item_id} label {label!r} is outside {list(LABELS)}",
            )
        family = _identifier(item["template_family"], f"{where}.template_family")
        split = item["split"]
        if split not in SPLITS:
            raise TaskForgeError(
                "malformed_input",
                f"{item_id} split {split!r} must be one of {list(SPLITS)}",
            )
        previous = families.get(family)
        if previous is not None and previous != split:
            raise TaskForgeError(
                "template_family_leak",
                f"template_family '{family}' appears in splits {previous} and {split}. "
                "Keep each template family, including its paraphrases, inside one split.",
            )
        families[family] = split
        split_counts[split] += 1
        normalized_items.append(
            {
                "item_id": item_id,
                "text": text,
                "label": label,
                "template_family": family,
                "split": split,
            }
        )
    empty = [split for split, count in split_counts.items() if count == 0]
    if empty:
        raise TaskForgeError(
            "incomplete_split",
            f"dataset is missing items for splits {empty}. "
            "train, validation, and evaluation are all required.",
        )
    normalized_items.sort(key=lambda row: row["item_id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA_VERSION,
        "label_set": list(LABELS),
        "items": normalized_items,
        "split_counts": split_counts,
    }


def validate_trace(document: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    """Validate a general-model trace against the dataset's evaluation ids."""
    _require_version(document, "trace")
    _require_keys(
        document,
        ("schema_version", "task_id", "task_schema_version", "model", "run", "results"),
        "trace",
    )
    if (
        document["task_id"] != dataset["task_id"]
        or document["task_schema_version"] != SCHEMA_VERSION
    ):
        raise TaskForgeError(
            "unsupported_task",
            "trace task_id and task_schema_version must match the dataset "
            f"({TASK_ID}, {SCHEMA_VERSION})",
        )
    model = document["model"]
    if not isinstance(model, dict):
        raise TaskForgeError("malformed_input", "trace.model must be an object")
    _require_keys(model, ("name", "revision", "provider", "hardware"), "trace.model")
    model_name = _string(model["name"], "trace.model.name", max_chars=80)
    revision = _string(model["revision"], "trace.model.revision", max_chars=80)
    provider = _string(model["provider"], "trace.model.provider", max_chars=80)
    hardware = _string(model["hardware"], "trace.model.hardware", max_chars=200)
    run = document["run"]
    if not isinstance(run, dict):
        raise TaskForgeError("malformed_input", "trace.run must be an object")
    _require_keys(
        run,
        ("seed", "started_at", "host", "wall_time_ms_total", "randomness"),
        "trace.run",
    )
    seed = run["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TaskForgeError("malformed_input", "trace.run.seed must be an integer")
    started_at = _string(run["started_at"], "trace.run.started_at", max_chars=40)
    host = _string(run["host"], "trace.run.host", max_chars=200)
    randomness = _string(run["randomness"], "trace.run.randomness", max_chars=200)
    total_ms = _nonnegative_number(run["wall_time_ms_total"], "trace.run.wall_time_ms_total")
    results = document["results"]
    if not isinstance(results, list):
        raise TaskForgeError("malformed_input", "trace.results must be a list")
    if len(results) > MAX_ITEMS:
        raise TaskForgeError(
            "input_too_large",
            f"trace.results has {len(results)} rows; the limit is {MAX_ITEMS}",
        )
    evaluation_ids = {item["item_id"] for item in dataset["items"] if item["split"] == "evaluation"}
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(results):
        where = f"results[{index}]"
        if not isinstance(row, dict):
            raise TaskForgeError("malformed_input", f"{where} must be an object")
        _require_keys(
            row,
            ("item_id", "output_label", "timeout", "scoring_status", "wall_time_ms", "confidence"),
            where,
        )
        item_id = _identifier(row["item_id"], f"{where}.item_id")
        if item_id in seen:
            raise TaskForgeError(
                "duplicate_id",
                f"trace item_id '{item_id}' is repeated",
            )
        seen.add(item_id)
        status = row["scoring_status"]
        if status not in SCORING_STATUSES:
            raise TaskForgeError(
                "malformed_input",
                f"{item_id} scoring_status {status!r} must be one of {list(SCORING_STATUSES)}",
            )
        timeout = row["timeout"]
        if not isinstance(timeout, bool):
            raise TaskForgeError("malformed_input", f"{item_id} timeout must be a boolean")
        label = row["output_label"]
        if status == "scored":
            if timeout or label not in LABELS:
                raise TaskForgeError(
                    "label_dictionary_mismatch",
                    f"{item_id} is scored but output_label {label!r} is not in {list(LABELS)} "
                    "with timeout false",
                )
        elif status == "timeout":
            if not timeout or label is not None:
                raise TaskForgeError(
                    "malformed_input",
                    f"{item_id} timeout rows need timeout true and output_label null",
                )
        else:
            if timeout or label is not None:
                raise TaskForgeError(
                    "malformed_input",
                    f"{item_id} {status} rows need timeout false and output_label null",
                )
        confidence = row["confidence"]
        if status == "scored":
            confidence = _unit_number(confidence, f"{item_id} confidence")
        elif confidence is not None:
            confidence = _unit_number(confidence, f"{item_id} confidence")
        normalized.append(
            {
                "item_id": item_id,
                "output_label": label if status == "scored" else None,
                "timeout": timeout,
                "scoring_status": status,
                "wall_time_ms": _nonnegative_number(row["wall_time_ms"], f"{item_id} wall_time_ms"),
                "confidence": confidence,
            }
        )
    missing = sorted(evaluation_ids - seen)
    extra = sorted(seen - evaluation_ids)
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing general-model results for {missing}")
        if extra:
            detail.append(f"trace ids that are not evaluation items: {extra}")
        code = "missing_general_result" if missing else "eval_id_mismatch"
        raise TaskForgeError(
            code,
            ". ".join(detail)
            + ". The trace must contain each evaluation id once and no other ids.",
        )
    normalized.sort(key=lambda row: row["item_id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "task_schema_version": SCHEMA_VERSION,
        "model": {
            "name": model_name,
            "revision": revision,
            "provider": provider,
            "hardware": hardware,
        },
        "run": {
            "seed": seed,
            "started_at": started_at,
            "host": host,
            "wall_time_ms_total": total_ms,
            "randomness": randomness,
        },
        "results": normalized,
    }


def validate_costs(document: dict[str, Any]) -> dict[str, Any]:
    """Validate a cost profile. Money fields must be decimal strings."""
    _require_version(document, "cost profile")
    _require_keys(
        document,
        (
            "schema_version",
            "profile_id",
            "currency",
            "horizon",
            "forecast_volume",
            "variable_cost_mode",
            "baseline",
            "specialist",
            "quality_gate",
        ),
        "cost profile",
        optional=("sensitivity_review_costs",),
    )
    profile_id = _identifier(document["profile_id"], "profile_id")
    currency = document["currency"]
    if currency not in CURRENCIES:
        raise TaskForgeError(
            "malformed_input",
            f"currency {currency!r} is not supported. Use {list(CURRENCIES)}.",
        )
    horizon = _string(document["horizon"], "horizon", max_chars=MAX_HORIZON_CHARS)
    volume = document["forecast_volume"]
    if isinstance(volume, bool) or not isinstance(volume, int) or not 1 <= volume <= MAX_FORECAST:
        raise TaskForgeError(
            "malformed_input",
            f"forecast_volume must be an integer from 1 to {MAX_FORECAST}",
        )
    mode = document["variable_cost_mode"]
    if mode not in VARIABLE_MODES:
        raise TaskForgeError(
            "malformed_input",
            f"variable_cost_mode {mode!r} must be one of {list(VARIABLE_MODES)}",
        )
    gate = document["quality_gate"]
    if not isinstance(gate, dict):
        raise TaskForgeError("malformed_input", "quality_gate must be an object")
    _require_keys(gate, ("min_macro_f1", "min_per_class_recall"), "quality_gate")
    sensitivity = document.get("sensitivity_review_costs")
    sensitivity_values: list[str] = []
    if sensitivity is not None:
        if not isinstance(sensitivity, list) or not 1 <= len(sensitivity) <= 6:
            raise TaskForgeError(
                "malformed_input",
                "sensitivity_review_costs must be a list of 1 to 6 decimal strings",
            )
        for index, entry in enumerate(sensitivity):
            parsed = parse_money(entry, f"sensitivity_review_costs[{index}]")
            sensitivity_values.append(format(parsed, "f"))
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_id": profile_id,
        "currency": currency,
        "horizon": horizon,
        "forecast_volume": volume,
        "variable_cost_mode": mode,
        "baseline": _party_costs(document["baseline"], "baseline", mode),
        "specialist": _party_costs(document["specialist"], "specialist", mode),
        "quality_gate": {
            "min_macro_f1": format(parse_unit_interval(gate["min_macro_f1"], "min_macro_f1"), "f"),
            "min_per_class_recall": format(
                parse_unit_interval(gate["min_per_class_recall"], "min_per_class_recall"),
                "f",
            ),
        },
        "sensitivity_review_costs": sensitivity_values,
    }


def _party_costs(document: Any, name: str, mode: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise TaskForgeError("malformed_input", f"{name} costs must be an object")
    required = (
        "fixed_cost",
        "components",
        "inference_cost_per_request",
        "review_cost_per_item",
        "provenance",
    )
    optional = ("modeled_variable_cost_per_request",) if mode == "modeled" else ()
    if mode == "modeled":
        required = required + ("modeled_variable_cost_per_request",)
    _require_keys(document, required, name, optional=optional if mode != "modeled" else ())
    components = document["components"]
    if not isinstance(components, dict):
        raise TaskForgeError("malformed_input", f"{name}.components must be an object")
    _require_keys(components, ("labeling", "training", "integration"), f"{name}.components")
    labeling = parse_money(components["labeling"], f"{name}.components.labeling")
    training = parse_money(components["training"], f"{name}.components.training")
    integration = parse_money(components["integration"], f"{name}.components.integration")
    fixed = parse_money(document["fixed_cost"], f"{name}.fixed_cost")
    if labeling + training + integration != fixed:
        raise TaskForgeError(
            "money_bounds",
            f"{name} components sum to {labeling + training + integration} but fixed_cost is {fixed}. "
            "Labeling, training, and integration must add up to the fixed cost.",
        )
    provenance = document["provenance"]
    if provenance not in PROVENANCE:
        raise TaskForgeError(
            "malformed_input",
            f"{name}.provenance {provenance!r} must be one of {list(PROVENANCE)}",
        )
    modeled = None
    if mode == "modeled":
        modeled = parse_money(
            document["modeled_variable_cost_per_request"],
            f"{name}.modeled_variable_cost_per_request",
        )
    return {
        "fixed_cost": format(fixed, "f"),
        "components": {
            "labeling": format(labeling, "f"),
            "training": format(training, "f"),
            "integration": format(integration, "f"),
        },
        "inference_cost_per_request": format(
            parse_money(
                document["inference_cost_per_request"], f"{name}.inference_cost_per_request"
            ),
            "f",
        ),
        "review_cost_per_item": format(
            parse_money(document["review_cost_per_item"], f"{name}.review_cost_per_item"),
            "f",
        ),
        "modeled_variable_cost_per_request": None if modeled is None else format(modeled, "f"),
        "provenance": provenance,
    }


def _nonnegative_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TaskForgeError("malformed_input", f"{where} must be a non-negative number")
    if value < 0 or value != value or value in (float("inf"), float("-inf")):
        raise TaskForgeError("malformed_input", f"{where} must be a finite number >= 0")
    return float(value)


def _unit_number(value: Any, where: str) -> float:
    number = _nonnegative_number(value, where)
    if number > 1:
        raise TaskForgeError("malformed_input", f"{where} must be between 0 and 1")
    return number


def validate_paths(
    dataset_path: Path,
    trace_path: Path | None = None,
    costs_path: Path | None = None,
) -> dict[str, Any]:
    """Validate files and return a small machine-readable summary."""
    dataset = validate_dataset(load_json_object(dataset_path))
    summary: dict[str, Any] = {
        "status": "valid",
        "dataset_items": len(dataset["items"]),
        "split_counts": dataset["split_counts"],
        "label_set": dataset["label_set"],
    }
    if trace_path is not None:
        trace = validate_trace(load_json_object(trace_path), dataset)
        summary["trace_results"] = len(trace["results"])
        summary["model"] = {
            "name": trace["model"]["name"],
            "revision": trace["model"]["revision"],
        }
    if costs_path is not None:
        costs = validate_costs(load_json_object(costs_path))
        summary["cost_profile"] = costs["profile_id"]
        summary["currency"] = costs["currency"]
        summary["variable_cost_mode"] = costs["variable_cost_mode"]
    return summary
