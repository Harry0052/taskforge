"""Pinned local generalist used to record the offline trace.

Revision 1.0.0 is a lexical scorer with a fixed keyword list. It is not trained
on the work-order set. Failure phrases are infrastructure outcomes of this
pinned run: the scorer returns no label, and those rows stay in the denominator.
"""

from __future__ import annotations

import re
import time
from typing import Any

MODEL_NAME = "lexical-generalist"
MODEL_REVISION = "1.0.0"
PROVIDER = "local"

# Whole-word cues. Specialist-only words (condenser, ballast, wax, valve,
# condensate, handler) are intentionally absent so the trained model can
# cover requests this generalist abstains on. "leak" is a plumbing cue and
# is the trap on hvac condensate requests.
KEYWORDS: dict[str, tuple[str, ...]] = {
    "custodial": ("mop", "trash", "spill", "restroom", "recycle"),
    "electrical": ("breaker", "outlet", "voltage", "switch", "circuit"),
    "hvac": ("thermostat", "airflow", "cooling", "heating", "duct"),
    "plumbing": ("faucet", "drain", "toilet", "clog", "pipe", "leak"),
}

FAILURE_PHRASES: tuple[tuple[str, str], ...] = (
    ("priority hold", "timeout"),
    ("unreadable attachment", "no_result"),
)

_TOKEN = re.compile(r"[a-z0-9]+")


def classify_text(text: str) -> dict[str, Any]:
    """Score one request. Returns label, status, timeout flag, and confidence."""
    lowered = text.lower()
    for phrase, status in FAILURE_PHRASES:
        if phrase in lowered:
            return {
                "output_label": None,
                "scoring_status": status,
                "timeout": status == "timeout",
                "confidence": None,
            }
    tokens = set(_TOKEN.findall(lowered))
    scores = {
        label: sum(1 for word in words if word in tokens) for label, words in KEYWORDS.items()
    }
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top_label, top_score = ranked[0]
    second_score = ranked[1][1]
    if top_score <= 0 or top_score == second_score:
        return {
            "output_label": None,
            "scoring_status": "abstain",
            "timeout": False,
            "confidence": 0.0,
        }
    confidence = top_score / (top_score + second_score)
    return {
        "output_label": top_label,
        "scoring_status": "scored",
        "timeout": False,
        "confidence": round(confidence, 4),
    }


def record_trace(
    evaluation_items: list[dict[str, str]],
    *,
    task_id: str,
    task_schema_version: str,
    schema_version: str,
    seed: int,
    host: str,
    started_at: str,
) -> dict[str, Any]:
    """Run the pinned generalist once and return a trace document."""
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    for item in evaluation_items:
        item_started = time.perf_counter()
        scored = classify_text(item["text"])
        elapsed_ms = (time.perf_counter() - item_started) * 1000.0
        results.append(
            {
                "item_id": item["item_id"],
                "output_label": scored["output_label"],
                "timeout": scored["timeout"],
                "scoring_status": scored["scoring_status"],
                "wall_time_ms": round(elapsed_ms, 3),
                "confidence": scored["confidence"],
            }
        )
    total_ms = (time.perf_counter() - started) * 1000.0
    results.sort(key=lambda row: row["item_id"])
    return {
        "schema_version": schema_version,
        "task_id": task_id,
        "task_schema_version": task_schema_version,
        "model": {
            "name": MODEL_NAME,
            "revision": MODEL_REVISION,
            "provider": PROVIDER,
            "hardware": host,
        },
        "run": {
            "seed": seed,
            "started_at": started_at,
            "host": host,
            "wall_time_ms_total": round(total_ms, 3),
            "randomness": "none; keyword scores are a pure function of the text",
        },
        "results": results,
    }
