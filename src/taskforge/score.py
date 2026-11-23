"""Score one model on a complete held-out id set.

Timeouts, abstentions, and no-results stay in each label's support. They are
not true positives and they are not predictions, so they reduce recall.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from taskforge.validate import LABELS

_SIX = Decimal("0.000001")


def score_predictions(
    rows: list[dict[str, Any]],
    *,
    gold_key: str = "gold",
    label_key: str = "predicted_label",
    status_key: str = "scoring_status",
) -> dict[str, Any]:
    """Macro-F1 and per-label recall. `rows` must already be the full eval set."""
    if not rows:
        raise ValueError("score_predictions requires at least one row")
    per_label: list[dict[str, Any]] = []
    f1_sum = Decimal(0)
    recalls: list[Decimal] = []
    for label in LABELS:
        support = sum(1 for row in rows if row[gold_key] == label)
        true_positives = sum(
            1
            for row in rows
            if row[gold_key] == label and row[status_key] == "scored" and row[label_key] == label
        )
        predicted = sum(
            1 for row in rows if row[status_key] == "scored" and row[label_key] == label
        )
        false_positives = predicted - true_positives
        precision = Decimal(true_positives) / Decimal(predicted) if predicted else Decimal(0)
        recall = Decimal(true_positives) / Decimal(support) if support else Decimal(0)
        if precision + recall == 0:
            f1 = Decimal(0)
        else:
            f1 = (Decimal(2) * precision * recall) / (precision + recall)
        f1_sum += f1
        recalls.append(recall)
        per_label.append(
            {
                "label": label,
                "support": support,
                "true_positives": true_positives,
                "false_positives": false_positives,
                "precision": _text(precision),
                "recall": _text(recall),
                "f1": _text(f1),
            }
        )
    status_counts = {status: 0 for status in ("scored", "abstain", "timeout", "no_result")}
    for row in rows:
        status_counts[row[status_key]] = status_counts.get(row[status_key], 0) + 1
    macro = f1_sum / Decimal(len(LABELS))
    return {
        "evaluated_items": len(rows),
        "macro_f1": _text(macro),
        "macro_f1_exact": macro,
        "min_recall_exact": min(recalls),
        "min_recall": _text(min(recalls)),
        "per_label": per_label,
        "status_counts": status_counts,
        "abstentions": status_counts.get("abstain", 0),
        "timeouts": status_counts.get("timeout", 0),
        "no_results": status_counts.get("no_result", 0),
        "denominator": "every evaluation item counts in its gold label support, including abstain, timeout, and no_result",
    }


def review_rate(status_counts: dict[str, int], evaluated_items: int) -> Decimal:
    """Share of rows that were not automatically scored."""
    reviewed = (
        status_counts.get("abstain", 0)
        + status_counts.get("timeout", 0)
        + status_counts.get("no_result", 0)
    )
    if evaluated_items <= 0:
        return Decimal(0)
    return Decimal(reviewed) / Decimal(evaluated_items)


def _text(value: Decimal) -> str:
    return format(value.quantize(_SIX, rounding=ROUND_HALF_EVEN), "f")
