from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta


METHODS = ("naive", "ma4", "ma8", "trend8")


def weekly_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        received = datetime.strptime(row["date_received"], "%Y-%m-%d").date()
        week = received - timedelta(days=received.weekday())
        counts[(week.isoformat(), row["product"])] += 1
    return [
        {"week": week, "product": product, "count": count}
        for (week, product), count in sorted(counts.items())
    ]


def _trend_prediction(history: list[float], window: int = 8) -> float:
    values = history[-window:]
    if len(values) < 2:
        return values[-1] if values else 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denominator = sum((index - x_mean) ** 2 for index in range(n))
    slope = sum(
        (index - x_mean) * (value - y_mean)
        for index, value in enumerate(values)
    ) / denominator
    return y_mean + slope * (n - x_mean)


def predict_next(history: list[float], method: str) -> float:
    if not history:
        return 0.0
    if method == "naive":
        return history[-1]
    if method in {"ma4", "ma8"}:
        window = int(method[2:])
        return sum(history[-window:]) / min(window, len(history))
    if method == "trend8":
        return _trend_prediction(history, window=8)
    raise ValueError(f"Unknown forecast method: {method}")


def forecast_values(values: list[int], horizon: int = 4, method: str = "ma4") -> list[int]:
    history = [float(value) for value in values]
    output = []
    for _ in range(horizon):
        prediction = max(0.0, predict_next(history, method))
        output.append(round(prediction))
        history.append(prediction)
    return output


def moving_average_forecast(values: list[int], horizon: int = 4, window: int = 4) -> list[int]:
    return forecast_values(values, horizon=horizon, method=f"ma{window}")


def walk_forward_errors(values: list[int], method: str, start: int = 8) -> list[float]:
    return [
        values[index] - predict_next([float(value) for value in values[:index]], method)
        for index in range(start, len(values))
    ]


def wape(values: list[int], method: str, start: int = 8) -> float:
    errors = walk_forward_errors(values, method, start=start)
    actual_total = sum(abs(value) for value in values[start:])
    return sum(abs(error) for error in errors) / actual_total if actual_total else 0.0


def backtest_wape(values: list[int], window: int = 4) -> float:
    if len(values) <= window:
        return 0.0
    return wape(values, f"ma{window}", start=window)


def select_method(values: list[int]) -> tuple[str, dict[str, float]]:
    scores = {method: wape(values, method) for method in METHODS}
    return min(scores, key=scores.get), scores


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1))
    return ordered[index]


def forecast_plan_by_product(
    weekly: list[dict[str, object]], horizon: int = 4
) -> dict[str, dict[str, object]]:
    observed_weeks = sorted({str(row["week"]) for row in weekly})
    if not observed_weeks:
        raise ValueError("weekly history is empty")
    first_week = datetime.strptime(observed_weeks[0], "%Y-%m-%d").date()
    last_week = datetime.strptime(observed_weeks[-1], "%Y-%m-%d").date()
    weeks = []
    cursor = first_week
    while cursor <= last_week:
        weeks.append(cursor.isoformat())
        cursor += timedelta(days=7)
    if len(weeks) < 12:
        raise ValueError("at least 12 weeks are required for forecast selection")
    products = sorted({str(row["product"]) for row in weekly})
    lookup = {
        (str(row["week"]), str(row["product"])): int(row["count"])
        for row in weekly
    }
    output: dict[str, dict[str, object]] = {}
    for product in products:
        values = [lookup.get((week, product), 0) for week in weeks]
        method, scores = select_method(values)
        point = forecast_values(values, horizon=horizon, method=method)
        error_band = _quantile(
            [abs(error) for error in walk_forward_errors(values, method)], 0.80
        )
        output[product] = {
            "method": method,
            "backtest_wape": scores[method],
            "naive_wape": scores["naive"],
            "candidate_wape": scores,
            "point": point,
            "lower": [max(0, round(value - error_band)) for value in point],
            "upper": [round(value + error_band) for value in point],
            "history": values,
        }
    return output


def forecast_by_product(
    weekly: list[dict[str, object]], horizon: int = 4
) -> dict[str, list[int]]:
    plan = forecast_plan_by_product(weekly, horizon=horizon)
    return {product: list(detail["point"]) for product, detail in plan.items()}
