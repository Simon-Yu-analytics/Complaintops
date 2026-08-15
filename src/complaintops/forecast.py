from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta


def weekly_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        date = datetime.strptime(row["date_received"], "%Y-%m-%d").date()
        week = date - timedelta(days=date.weekday())
        counts[(week.isoformat(), row["product"])] += 1
    return [
        {"week": week, "product": product, "count": count}
        for (week, product), count in sorted(counts.items())
    ]


def moving_average_forecast(values: list[int], horizon: int = 4, window: int = 4) -> list[int]:
    if not values:
        return [0] * horizon
    history = [float(value) for value in values]
    forecasts = []
    for _ in range(horizon):
        prediction = sum(history[-window:]) / min(window, len(history))
        forecasts.append(max(0, round(prediction)))
        history.append(prediction)
    return forecasts


def forecast_by_product(weekly: list[dict[str, object]], horizon: int = 4) -> dict[str, list[int]]:
    series: dict[str, list[int]] = defaultdict(list)
    weeks = sorted({str(row["week"]) for row in weekly})
    lookup = {(str(row["week"]), str(row["product"])): int(row["count"]) for row in weekly}
    products = sorted({str(row["product"]) for row in weekly})
    for product in products:
        series[product] = [lookup.get((week, product), 0) for week in weeks]
    return {product: moving_average_forecast(values, horizon=horizon) for product, values in series.items()}


def backtest_wape(values: list[int], window: int = 4) -> float:
    if len(values) <= window:
        return 0.0
    absolute_error = 0.0
    actual_total = 0.0
    for index in range(window, len(values)):
        prediction = sum(values[index - window:index]) / window
        absolute_error += abs(values[index] - prediction)
        actual_total += abs(values[index])
    return absolute_error / actual_total if actual_total else 0.0

