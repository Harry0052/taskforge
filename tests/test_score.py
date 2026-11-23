"""Hand-checked scoring: failures stay in the support denominator."""

from __future__ import annotations

from taskforge.score import score_predictions


def test_timeout_and_abstain_remain_in_support() -> None:
    rows = [
        {"gold": "hvac", "predicted_label": "hvac", "scoring_status": "scored"},
        {"gold": "plumbing", "predicted_label": None, "scoring_status": "abstain"},
        {"gold": "electrical", "predicted_label": None, "scoring_status": "timeout"},
        {"gold": "custodial", "predicted_label": "custodial", "scoring_status": "scored"},
    ]
    metrics = score_predictions(rows)
    by_label = {row["label"]: row for row in metrics["per_label"]}
    assert metrics["evaluated_items"] == 4
    assert metrics["abstentions"] == 1
    assert metrics["timeouts"] == 1
    assert metrics["no_results"] == 0
    for label in ("hvac", "plumbing", "electrical", "custodial"):
        assert by_label[label]["support"] == 1
    assert by_label["hvac"]["recall"] == "1.000000"
    assert by_label["plumbing"]["recall"] == "0.000000"
    assert by_label["electrical"]["recall"] == "0.000000"
    assert by_label["custodial"]["recall"] == "1.000000"
    assert metrics["macro_f1"] == "0.500000"
