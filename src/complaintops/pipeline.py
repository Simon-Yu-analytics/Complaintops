from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .classifier import (
    MultinomialNB,
    choose_confidence_threshold,
    classification_metrics,
    selective_routing_metrics,
)
from .data import load_complaints
from .forecast import forecast_plan_by_product, weekly_counts
from .optimize import staffing_plan


ROOT = Path(__file__).resolve().parents[2]


def build_dashboard_model(
    model: MultinomialNB,
    threshold: float,
    training_records: int,
) -> dict[str, object]:
    """Export the fitted baseline for transparent, browser-side inference."""
    labels = sorted(model.class_counts)
    return {
        "version": 1,
        "mode": "synthetic-sample",
        "alpha": model.alpha,
        "threshold": round(threshold, 4),
        "training_records": training_records,
        "vocabulary": sorted(model.vocabulary),
        "classes": [
            {
                "label": label,
                "documents": model.class_counts[label],
                "total_tokens": model.total_tokens[label],
                "token_counts": dict(sorted(model.token_counts[label].items())),
            }
            for label in labels
        ],
    }


def _round_output(value: object) -> object:
    """Round report floats recursively while preserving the output structure."""
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, list):
        return [_round_output(item) for item in value]
    if isinstance(value, dict):
        return {key: _round_output(item) for key, item in value.items()}
    return value


def temporal_split(
    rows: list[dict[str, str]], test_fraction: float = 0.25
) -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    """Hold out the newest dates so evaluation resembles a future deployment."""
    if not 0 < test_fraction < 1 or len(rows) < 2:
        raise ValueError("temporal split requires at least two rows and 0 < fraction < 1")
    ordered = sorted(rows, key=lambda row: (row["date_received"], row["complaint_id"]))
    cut = max(1, min(len(ordered) - 1, round(len(ordered) * (1 - test_fraction))))
    cutoff_date = ordered[cut]["date_received"]
    train = [row for row in ordered if row["date_received"] < cutoff_date]
    test = [row for row in ordered if row["date_received"] >= cutoff_date]
    if not train or not test:
        raise ValueError("temporal split produced an empty partition")
    return train, test, cutoff_date


def run() -> dict[str, object]:
    data_path = ROOT / "data" / "sample" / "complaints.csv"
    rows = load_complaints(data_path)
    development, test, cutoff_date = temporal_split(rows)
    train, calibration, calibration_cutoff = temporal_split(
        development, test_fraction=0.20
    )
    all_labels = {row["product"] for row in rows}
    if {row["product"] for row in train} != all_labels:
        raise ValueError("training window does not contain every product class")
    model = MultinomialNB(alpha=0.8).fit(
        [row["narrative"] for row in train], [row["product"] for row in train]
    )
    calibration_probabilities = [
        model.predict_proba(row["narrative"]) for row in calibration
    ]
    calibration_predictions = [
        max(item, key=item.get) for item in calibration_probabilities
    ]
    calibration_confidences = [max(item.values()) for item in calibration_probabilities]
    threshold_policy = choose_confidence_threshold(
        [row["product"] for row in calibration],
        calibration_predictions,
        calibration_confidences,
        target_accuracy=0.85,
        minimum_coverage=0.50,
    )

    probabilities = [model.predict_proba(row["narrative"]) for row in test]
    predictions = [max(item, key=item.get) for item in probabilities]
    confidences = [max(item.values()) for item in probabilities]
    actual = [row["product"] for row in test]
    metrics = classification_metrics(actual, predictions)
    routing = selective_routing_metrics(
        actual,
        predictions,
        confidences,
        threshold=float(threshold_policy["threshold"]),
    )
    curve_thresholds = sorted(
        {
            0.50,
            0.60,
            0.70,
            0.80,
            0.85,
            0.90,
            0.93,
            0.95,
            round(float(threshold_policy["threshold"]), 4),
            0.97,
            0.99,
        }
    )
    calibration_curve = [
        {
            key: round(value, 4) if isinstance(value, float) else value
            for key, value in selective_routing_metrics(
                [row["product"] for row in calibration],
                calibration_predictions,
                calibration_confidences,
                threshold,
            ).items()
        }
        for threshold in curve_thresholds
    ]

    weekly = weekly_counts(rows)
    forecast_plan = forecast_plan_by_product(weekly, horizon=4)
    forecasts = {
        product: list(detail["point"])
        for product, detail in forecast_plan.items()
    }
    upper_forecasts = {
        product: list(detail["upper"])
        for product, detail in forecast_plan.items()
    }
    staffing = staffing_plan(forecasts, upper_forecast=upper_forecasts)
    product_counts = Counter(row["product"] for row in rows)
    issue_counts = Counter(row["issue"] for row in rows)

    result = {
        "mode": "synthetic-sample",
        "records": len(rows),
        "date_range": [
            min(row["date_received"] for row in rows),
            max(row["date_received"] for row in rows),
        ],
        "classification": {
            **{key: round(value, 4) for key, value in metrics.items()},
            "test_records": len(test),
            "train_records": len(train),
            "calibration_records": len(calibration),
            "calibration_cutoff_date": calibration_cutoff,
            "cutoff_date": cutoff_date,
            "threshold_policy": {
                key: round(value, 4) if isinstance(value, float) else value
                for key, value in threshold_policy.items()
            },
            "calibration_curve": calibration_curve,
            "selective_routing": {
                key: round(value, 4) if isinstance(value, float) else value
                for key, value in routing.items()
            },
        },
        "product_counts": dict(product_counts.most_common()),
        "top_issues": dict(issue_counts.most_common(8)),
        "weekly_history": weekly,
        "forecast": forecasts,
        "forecast_detail": {
            product: {
                key: _round_output(value)
                for key, value in detail.items()
                if key != "history"
            }
            for product, detail in forecast_plan.items()
        },
        "forecast_wape": {
            product: round(float(detail["backtest_wape"]), 4)
            for product, detail in forecast_plan.items()
        },
        "staffing": staffing,
    }
    targets = [
        ROOT / "dashboard" / "data" / "results.json",
        ROOT / "reports" / "results.json",
    ]
    encoded = json.dumps(result, indent=2)
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded + "\n", encoding="utf-8")
    dashboard_model = build_dashboard_model(
        model,
        threshold=float(threshold_policy["threshold"]),
        training_records=len(train),
    )
    encoded_model = json.dumps(dashboard_model, indent=2)
    (ROOT / "dashboard" / "data" / "model.json").write_text(
        encoded_model + "\n",
        encoding="utf-8",
    )
    (ROOT / "dashboard" / "data" / "app-data.js").write_text(
        f"window.COMPLAINTOPS_RESULTS = {encoded};\n"
        f"window.COMPLAINTOPS_MODEL = {encoded_model};\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(rows),
                "classification": result["classification"],
                "total_agents": staffing["total_agents"],
            },
            indent=2,
        )
    )
    return result


if __name__ == "__main__":
    run()
