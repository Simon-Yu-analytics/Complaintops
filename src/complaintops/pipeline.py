from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .classifier import MultinomialNB, classification_metrics
from .data import load_complaints
from .forecast import backtest_wape, forecast_by_product, weekly_counts
from .optimize import staffing_plan


ROOT = Path(__file__).resolve().parents[2]


def stratified_split(rows: list[dict[str, str]], test_fraction: float = 0.25, seed: int = 42):
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["product"]].append(row)
    train, test = [], []
    for grouped in groups.values():
        rng.shuffle(grouped)
        cut = max(1, round(len(grouped) * test_fraction))
        test.extend(grouped[:cut])
        train.extend(grouped[cut:])
    return train, test


def run() -> dict[str, object]:
    data_path = ROOT / "data" / "sample" / "complaints.csv"
    rows = load_complaints(data_path)
    train, test = stratified_split(rows)
    model = MultinomialNB(alpha=0.8).fit(
        [row["narrative"] for row in train], [row["product"] for row in train]
    )
    predictions = [model.predict(row["narrative"]) for row in test]
    metrics = classification_metrics([row["product"] for row in test], predictions)

    weekly = weekly_counts(rows)
    forecasts = forecast_by_product(weekly, horizon=4)
    values_by_product: dict[str, list[int]] = defaultdict(list)
    weeks = sorted({str(row["week"]) for row in weekly})
    lookup = {(str(row["week"]), str(row["product"])): int(row["count"]) for row in weekly}
    for product in sorted(forecasts):
        values_by_product[product] = [lookup.get((week, product), 0) for week in weeks]
    forecast_wape = {
        product: backtest_wape(values) for product, values in values_by_product.items()
    }
    staffing = staffing_plan(forecasts)
    product_counts = Counter(row["product"] for row in rows)
    issue_counts = Counter(row["issue"] for row in rows)

    result = {
        "mode": "synthetic-sample",
        "records": len(rows),
        "date_range": [min(row["date_received"] for row in rows), max(row["date_received"] for row in rows)],
        "classification": {**{key: round(value, 4) for key, value in metrics.items()}, "test_records": len(test)},
        "product_counts": dict(product_counts.most_common()),
        "top_issues": dict(issue_counts.most_common(8)),
        "weekly_history": weekly,
        "forecast": forecasts,
        "forecast_wape": {key: round(value, 4) for key, value in forecast_wape.items()},
        "staffing": staffing,
    }
    targets = [ROOT / "dashboard" / "data" / "results.json", ROOT / "reports" / "results.json"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(rows), "classification": result["classification"], "total_agents": staffing["total_agents"]}, indent=2))
    return result


if __name__ == "__main__":
    run()

