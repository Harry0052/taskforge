"""Train the CPU specialist and export coefficients as data, not a pickle."""

from __future__ import annotations

import os
import time
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from taskforge.score import score_predictions
from taskforge.validate import LABELS

SEED = 0
THRESHOLDS: tuple[float, ...] = tuple(step / 20 for step in range(0, 20))


def train_specialist(
    train_items: list[dict[str, str]],
    validation_items: list[dict[str, str]],
) -> dict[str, Any]:
    """Fit a linear classifier and freeze the confidence cutoff on validation."""
    started = time.perf_counter()
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        token_pattern=r"[a-z0-9]+",
        min_df=1,
    )
    train_matrix = vectorizer.fit_transform([item["text"] for item in train_items])
    classifier = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=500,
        random_state=SEED,
    )
    classifier.fit(train_matrix, [item["label"] for item in train_items])
    train_ms = (time.perf_counter() - started) * 1000.0

    best_threshold = 0.0
    best_f1 = None
    best_metrics: dict[str, Any] | None = None
    for threshold in THRESHOLDS:
        metrics = _metrics_at(vectorizer, classifier, validation_items, threshold)
        macro = metrics["macro_f1_exact"]
        if best_f1 is None or macro > best_f1 or (macro == best_f1 and threshold < best_threshold):
            best_f1 = macro
            best_threshold = threshold
            best_metrics = metrics
    assert best_metrics is not None
    public_validation = _public_metrics(best_metrics)
    return {
        "vectorizer": vectorizer,
        "classifier": classifier,
        "threshold": best_threshold,
        "validation_metrics": public_validation,
        "train_wall_time_ms": round(train_ms, 3),
        "train_items": len(train_items),
        "validation_items": len(validation_items),
        "seed": SEED,
        "export": export_coefficients(vectorizer, classifier),
    }


def predict_items(
    model: dict[str, Any],
    items: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], float]:
    """Apply the frozen threshold. Returns rows aligned to `items` and wall time."""
    started = time.perf_counter()
    predictions = _predict(
        model["vectorizer"],
        model["classifier"],
        [item["text"] for item in items],
        model["threshold"],
    )
    elapsed = (time.perf_counter() - started) * 1000.0
    rows: list[dict[str, Any]] = []
    for item, predicted in zip(items, predictions, strict=True):
        label, confidence = predicted
        status = "scored" if label is not None else "abstain"
        rows.append(
            {
                "item_id": item["item_id"],
                "gold": item["label"],
                "text": item["text"],
                "template_family": item["template_family"],
                "predicted_label": label,
                "scoring_status": status,
                "confidence": None if confidence is None else round(confidence, 6),
            }
        )
    return rows, round(elapsed, 3)


def export_coefficients(
    vectorizer: TfidfVectorizer, classifier: LogisticRegression
) -> dict[str, Any]:
    """JSON-safe coefficients. Callers must not unpickle this document."""
    vocabulary = {term: int(index) for term, index in sorted(vectorizer.vocabulary_.items())}
    return {
        "format": "taskforge-linear-export",
        "format_version": "1.0.0",
        "note": "Inspection artifact. TaskForge retrains from the fixture; it does not load this file.",
        "labels": list(LABELS),
        "classes": [str(label) for label in classifier.classes_],
        "vocabulary": vocabulary,
        "idf": [float(value) for value in vectorizer.idf_],
        "coef": [[float(value) for value in row] for row in classifier.coef_],
        "intercept": [float(value) for value in classifier.intercept_],
    }


def _predict(
    vectorizer: TfidfVectorizer,
    classifier: LogisticRegression,
    texts: list[str],
    threshold: float,
) -> list[tuple[str | None, float | None]]:
    if not texts:
        return []
    probabilities = classifier.predict_proba(vectorizer.transform(texts))
    classes = [str(label) for label in classifier.classes_]
    chosen: list[tuple[str | None, float | None]] = []
    for row in probabilities:
        index = int(row.argmax())
        confidence = float(row[index])
        if confidence < threshold:
            chosen.append((None, confidence))
        else:
            chosen.append((classes[index], confidence))
    return chosen


def _metrics_at(
    vectorizer: TfidfVectorizer,
    classifier: LogisticRegression,
    items: list[dict[str, str]],
    threshold: float,
) -> dict[str, Any]:
    predictions = _predict(
        vectorizer,
        classifier,
        [item["text"] for item in items],
        threshold,
    )
    rows = []
    for item, (label, _confidence) in zip(items, predictions, strict=True):
        rows.append(
            {
                "gold": item["label"],
                "predicted_label": label,
                "scoring_status": "scored" if label is not None else "abstain",
            }
        )
    return score_predictions(rows)


def _public_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if not key.endswith("_exact")}
