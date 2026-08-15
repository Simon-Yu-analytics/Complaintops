from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from complaintops.classifier import MultinomialNB  # noqa: E402
from complaintops.data import load_complaints  # noqa: E402
from complaintops.pipeline import temporal_split  # noqa: E402


PLOTS = ROOT / "plots"
RESULTS_PATH = ROOT / "dashboard" / "data" / "results.json"
DATA_PATH = ROOT / "data" / "sample" / "complaints.csv"

INK = "#171B1A"
MUTED = "#65706C"
PAPER = "#F4F6F3"
WHITE = "#FFFFFF"
GRID = "#DDE3DF"
GREEN = "#16483B"
GREEN_2 = "#2F735E"
LIME = "#D7FF45"
ORANGE = "#FF9D66"
BLUE = "#5D8FE8"
RED = "#D75959"
PURPLE = "#8D70D8"
TEAL = "#55B6A9"

SERIES_COLORS = [GREEN, BLUE, ORANGE, PURPLE, TEAL]
METHOD_COLORS = {"naive": GREEN, "ma4": BLUE, "ma8": ORANGE, "trend8": PURPLE}
SHORT = {
    "Checking or savings account": "Checking / savings",
    "Credit card": "Credit card",
    "Credit reporting": "Credit reporting",
    "Debt collection": "Debt collection",
    "Mortgage": "Mortgage",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "Arial Bold.ttf" if bold else "Arial.ttf"
    candidates = [
        Path("/System/Library/Fonts/Supplemental") / filename,
        Path("/Library/Fonts") / filename,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> float:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and text_width(draw, trial, fnt) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def chart_base(title: str, subtitle: str, size: tuple[int, int] = (1600, 1000)) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", size, PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 18, size[1]), fill=LIME)
    draw.text((86, 58), title, font=font(48, True), fill=INK)
    draw.text((88, 122), subtitle, font=font(25), fill=MUTED)
    draw.text((88, size[1] - 50), "ComplaintOps  |  Synthetic demonstration data", font=font(18), fill=MUTED)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    image.save(PLOTS / name, format="PNG", optimize=True)


def axis_label(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, *, anchor: str = "mm", color: str = MUTED, size: int = 20) -> None:
    draw.text(xy, value, font=font(size), fill=color, anchor=anchor)


def draw_product_mix(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Complaint portfolio mix",
        "Volume concentration determines where routing errors and staffing gaps matter most.",
    )
    counts = list(results["product_counts"].items())
    total = sum(value for _, value in counts)
    left, top, right, bottom = 390, 220, 1480, 865
    max_value = max(value for _, value in counts)
    for grid_value in range(0, max_value + 1, 500):
        x = left + (right - left) * grid_value / max_value
        draw.line((x, top, x, bottom), fill=GRID, width=2)
        axis_label(draw, (x, bottom + 28), f"{grid_value:,}")
    row_height = (bottom - top) / len(counts)
    for index, (product, value) in enumerate(counts):
        y = top + index * row_height + 18
        bar_bottom = y + 68
        width = (right - left) * value / max_value
        color = SERIES_COLORS[index]
        draw.rounded_rectangle((left, y, left + width, bar_bottom), radius=14, fill=color)
        draw.text((left - 24, (y + bar_bottom) / 2), SHORT[product], font=font(25, True), fill=INK, anchor="rm")
        label = f"{value:,}  |  {value / total:.1%}"
        label_color = WHITE if width > 260 else INK
        x_label = left + width - 18 if width > 260 else left + width + 18
        anchor = "rm" if width > 260 else "lm"
        draw.text((x_label, (y + bar_bottom) / 2), label, font=font(23, True), fill=label_color, anchor=anchor)
    draw.text((left, 902), f"Total complaints: {total:,}", font=font(22, True), fill=GREEN)
    save(image, "01_complaint_portfolio_mix.png")


def draw_weekly_trends(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Weekly complaint demand",
        "Fifty-two weeks of synthetic volume reveal queue-specific scale and variability.",
    )
    history: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for row in results["weekly_history"]:
        history[row["product"]].append((row["week"], row["count"]))
    left, top, right, bottom = 110, 250, 1490, 825
    max_value = max(value for rows in history.values() for _, value in rows)
    y_max = int(math.ceil(max_value / 10) * 10)
    for tick in range(0, y_max + 1, 10):
        y = bottom - (bottom - top) * tick / y_max
        draw.line((left, y, right, y), fill=GRID, width=2)
        axis_label(draw, (left - 24, y), str(tick), anchor="rm")
    weeks = sorted({week for rows in history.values() for week, _ in rows})
    for i, week in enumerate(weeks):
        if i % 8 == 0 or (i == len(weeks) - 1 and i % 8 > 2):
            x = left + (right - left) * i / (len(weeks) - 1)
            axis_label(draw, (x, bottom + 34), datetime.strptime(week, "%Y-%m-%d").strftime("%b %Y"), size=18)
    for index, product in enumerate(sorted(history)):
        rows = sorted(history[product])
        points = [
            (
                left + (right - left) * i / (len(rows) - 1),
                bottom - (bottom - top) * value / y_max,
            )
            for i, (_, value) in enumerate(rows)
        ]
        draw.line(points, fill=SERIES_COLORS[index], width=5, joint="curve")
        for x, y in points[::8]:
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=SERIES_COLORS[index])
    legend_x, legend_y = 120, 200
    for index, product in enumerate(sorted(history)):
        x = legend_x + index * 285
        draw.line((x, legend_y, x + 34, legend_y), fill=SERIES_COLORS[index], width=7)
        draw.text((x + 45, legend_y), SHORT[product], font=font(19, True), fill=INK, anchor="lm")
    save(image, "02_weekly_demand_trends.png")


def build_model_analysis() -> dict[str, object]:
    rows = load_complaints(DATA_PATH)
    development, test, cutoff = temporal_split(rows)
    train, calibration, calibration_cutoff = temporal_split(development, test_fraction=0.20)
    model = MultinomialNB(alpha=0.8).fit(
        [row["narrative"] for row in train], [row["product"] for row in train]
    )
    probabilities = [model.predict_proba(row["narrative"]) for row in test]
    predicted = [max(scores, key=scores.get) for scores in probabilities]
    actual = [row["product"] for row in test]
    confidences = [max(scores.values()) for scores in probabilities]
    labels = sorted(set(actual) | set(predicted))
    matrix = [[0 for _ in labels] for _ in labels]
    for actual_label, predicted_label in zip(actual, predicted):
        matrix[labels.index(actual_label)][labels.index(predicted_label)] += 1
    class_metrics: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = sum(a == label and p == label for a, p in zip(actual, predicted))
        fp = sum(a != label and p == label for a, p in zip(actual, predicted))
        fn = sum(a == label and p != label for a, p in zip(actual, predicted))
        support = sum(a == label for a in actual)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        class_metrics[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
    correct_confidence = [c for a, p, c in zip(actual, predicted, confidences) if a == p]
    error_confidence = [c for a, p, c in zip(actual, predicted, confidences) if a != p]
    return {
        "labels": labels,
        "confusion_matrix": matrix,
        "class_metrics": class_metrics,
        "train_records": len(train),
        "calibration_records": len(calibration),
        "test_records": len(test),
        "start_date": min(row["date_received"] for row in rows),
        "end_date": max(row["date_received"] for row in rows),
        "calibration_cutoff_date": calibration_cutoff,
        "test_cutoff_date": cutoff,
        "correct_confidence_mean": round(sum(correct_confidence) / len(correct_confidence), 4),
        "error_confidence_mean": round(sum(error_confidence) / len(error_confidence), 4),
    }


def draw_split_timeline(model_analysis: dict[str, object]) -> None:
    image, draw = chart_base(
        "Chronological validation design",
        "The threshold is chosen on calibration data and frozen before the newest test period.",
    )
    start = datetime.strptime(model_analysis["start_date"], "%Y-%m-%d").date()
    end = datetime.strptime(model_analysis["end_date"], "%Y-%m-%d").date()
    calibration_start = datetime.strptime(model_analysis["calibration_cutoff_date"], "%Y-%m-%d").date()
    test_start = datetime.strptime(model_analysis["test_cutoff_date"], "%Y-%m-%d").date()
    total_days = (end - start).days
    left, right = 130, 1470
    bar_top, bar_bottom = 320, 470

    def x_for(date) -> float:
        return left + (right - left) * (date - start).days / total_days

    segments = [
        (start, calibration_start, GREEN, "TRAIN", model_analysis["train_records"]),
        (calibration_start, test_start, ORANGE, "CALIBRATION", model_analysis["calibration_records"]),
        (test_start, end + timedelta(days=1), BLUE, "FINAL TEST", model_analysis["test_records"]),
    ]
    for seg_start, seg_end, color, label, count in segments:
        x1, x2 = x_for(seg_start), min(right, x_for(min(seg_end, end)))
        draw.rounded_rectangle((x1, bar_top, x2, bar_bottom), radius=14, fill=color)
        draw.text(((x1 + x2) / 2, 370), label, font=font(26, True), fill=WHITE, anchor="mm")
        draw.text(((x1 + x2) / 2, 418), f"{count:,} records", font=font(23), fill=WHITE, anchor="mm")
    dates = [(start, "Jan 2025"), (calibration_start, "16 Aug 2025"), (test_start, "11 Oct 2025"), (end, "4 Jan 2026")]
    for date, label in dates:
        x = x_for(date)
        draw.line((x, bar_bottom + 10, x, bar_bottom + 32), fill=INK, width=3)
        axis_label(draw, (x, bar_bottom + 60), label, size=20)
    callouts = [
        (GREEN, "1", "Fit vocabulary and class likelihoods", "Only the oldest observations train the model."),
        (ORANGE, "2", "Choose the automation threshold", "Target at least 85% routed accuracy with at least 50% coverage."),
        (BLUE, "3", "Report untouched future performance", "No threshold or model choice is made on the final test window."),
    ]
    for index, (color, number, title, body) in enumerate(callouts):
        x = 130 + index * 455
        y = 620
        draw.rounded_rectangle((x, y, x + 410, y + 185), radius=20, fill=WHITE, outline=GRID, width=2)
        draw.ellipse((x + 24, y + 25, x + 76, y + 77), fill=color)
        draw.text((x + 50, y + 51), number, font=font(24, True), fill=WHITE, anchor="mm")
        draw.text((x + 95, y + 30), title, font=font(22, True), fill=INK)
        for line_i, line in enumerate(wrap(draw, body, font(19), 365)):
            draw.text((x + 26, y + 96 + line_i * 27), line, font=font(19), fill=MUTED)
    save(image, "03_temporal_validation_design.png")


def draw_confusion_matrix(model_analysis: dict[str, object]) -> None:
    image, draw = chart_base(
        "Routing confusion matrix",
        "Rows are actual queues; cells show row share with record count on the final temporal test set.",
        size=(1600, 1120),
    )
    labels = model_analysis["labels"]
    matrix = model_analysis["confusion_matrix"]
    left, top = 470, 270
    cell = 118
    max_share = 1.0
    for i, row in enumerate(matrix):
        row_total = sum(row)
        draw.text((left - 28, top + i * cell + cell / 2), SHORT[labels[i]], font=font(22, True), fill=INK, anchor="rm")
        for j, value in enumerate(row):
            share = value / row_total if row_total else 0
            x1, y1 = left + j * cell, top + i * cell
            blend = share / max_share
            base = (244, 246, 243)
            target = (22, 72, 59)
            rgb = tuple(round(base[k] + (target[k] - base[k]) * blend) for k in range(3))
            fill = "#%02x%02x%02x" % rgb
            draw.rectangle((x1, y1, x1 + cell - 3, y1 + cell - 3), fill=fill)
            color = WHITE if share > 0.47 else INK
            draw.text((x1 + cell / 2, y1 + 42), f"{share:.0%}", font=font(24, True), fill=color, anchor="mm")
            draw.text((x1 + cell / 2, y1 + 78), f"n={value}", font=font(17), fill=color, anchor="mm")
    matrix_headers = {
        "Checking or savings account": "Checking /\nsavings",
        "Credit card": "Credit\ncard",
        "Credit reporting": "Credit\nreporting",
        "Debt collection": "Debt\ncollection",
        "Mortgage": "Mortgage",
    }
    for j, label in enumerate(labels):
        draw.multiline_text(
            (left + j * cell + cell / 2, top - 75),
            matrix_headers[label],
            font=font(16, True),
            fill=INK,
            anchor="ma",
            align="center",
            spacing=3,
        )
    draw.text((left + cell * 2.5, 950), "Predicted queue", font=font(23, True), fill=GREEN, anchor="mm")
    draw.text((140, top + cell * 2.5), "Actual queue", font=font(23, True), fill=GREEN, anchor="mm")
    save(image, "04_routing_confusion_matrix.png")


def draw_class_performance(model_analysis: dict[str, object]) -> None:
    image, draw = chart_base(
        "Routing quality by product queue",
        "Macro-F1 prevents the largest class from hiding weaker performance in smaller queues.",
    )
    labels = model_analysis["labels"]
    metrics = model_analysis["class_metrics"]
    left, top, right, bottom = 190, 265, 1490, 825
    for tick in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y = bottom - (bottom - top) * tick
        draw.line((left, y, right, y), fill=GRID, width=2)
        axis_label(draw, (left - 28, y), f"{tick:.0%}", anchor="rm")
    group_width = (right - left) / len(labels)
    bar_width = 46
    series = [("Precision", "precision", GREEN), ("Recall", "recall", BLUE), ("F1", "f1", ORANGE)]
    for group_i, label in enumerate(labels):
        center = left + group_width * (group_i + 0.5)
        for series_i, (_, key, color) in enumerate(series):
            value = metrics[label][key]
            x1 = center + (series_i - 1) * 58 - bar_width / 2
            y1 = bottom - (bottom - top) * value
            draw.rounded_rectangle((x1, y1, x1 + bar_width, bottom), radius=8, fill=color)
            draw.text((x1 + bar_width / 2, y1 - 14), f"{value:.0%}", font=font(17, True), fill=INK, anchor="ms")
        draw.text((center, bottom + 28), SHORT[label].replace(" ", "\n", 1), font=font(19, True), fill=INK, anchor="ma", align="center")
        draw.text((center, bottom + 86), f"n={metrics[label]['support']}", font=font(17), fill=MUTED, anchor="ma")
    for index, (name, _, color) in enumerate(series):
        x = 560 + index * 190
        draw.rounded_rectangle((x, 205, x + 36, 229), radius=5, fill=color)
        draw.text((x + 48, 217), name, font=font(20, True), fill=INK, anchor="lm")
    save(image, "05_class_performance.png")


def draw_threshold_tradeoff(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Confidence threshold trade-off",
        "A higher threshold improves automated-route accuracy but sends more cases to human review.",
    )
    curve = results["classification"]["calibration_curve"]
    frozen = results["classification"]["threshold_policy"]["threshold"]
    left, top, right, bottom = 150, 275, 1460, 820
    x_min, x_max = 0.5, 1.0
    y_min, y_max = 0.0, 1.0
    for tick in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y = bottom - (bottom - top) * tick
        draw.line((left, y, right, y), fill=GRID, width=2)
        axis_label(draw, (left - 25, y), f"{tick:.0%}", anchor="rm")
    for tick in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        x = left + (right - left) * (tick - x_min) / (x_max - x_min)
        axis_label(draw, (x, bottom + 35), f"{tick:.2f}")
    series = [("Auto-route accuracy", "accuracy", GREEN), ("Coverage", "coverage", BLUE), ("Review rate", "review_rate", ORANGE)]
    for name, key, color in series:
        points = []
        for item in curve:
            x = left + (right - left) * (item["threshold"] - x_min) / (x_max - x_min)
            y = bottom - (bottom - top) * (item[key] - y_min) / (y_max - y_min)
            points.append((x, y))
        draw.line(points, fill=color, width=6, joint="curve")
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline=WHITE, width=2)
    target_y = bottom - (bottom - top) * 0.85
    draw.line((left, target_y, right, target_y), fill=RED, width=3)
    draw.text((right - 8, target_y - 10), "85% policy target", font=font(18, True), fill=RED, anchor="rs")
    frozen_x = left + (right - left) * (frozen - x_min) / (x_max - x_min)
    draw.line((frozen_x, top, frozen_x, bottom), fill=INK, width=3)
    draw.rounded_rectangle((frozen_x - 132, top - 48, frozen_x + 132, top - 6), radius=10, fill=INK)
    draw.text((frozen_x, top - 27), f"Frozen threshold {frozen:.4f}", font=font(18, True), fill=WHITE, anchor="mm")
    for index, (name, _, color) in enumerate(series):
        x = 400 + index * 310
        draw.line((x, 215, x + 40, 215), fill=color, width=7)
        draw.text((x + 52, 215), name, font=font(20, True), fill=INK, anchor="lm")
    save(image, "06_threshold_tradeoff.png")


def draw_forecast_comparison(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Forecast model comparison",
        "Each queue selects the lowest walk-forward WAPE; complexity is used only when it improves the baseline.",
    )
    products = sorted(results["forecast_detail"])
    methods = ["naive", "ma4", "ma8", "trend8"]
    left, top = 420, 260
    cell_w, cell_h = 245, 105
    max_wape = max(
        results["forecast_detail"][product]["candidate_wape"][method]
        for product in products for method in methods
    )
    for j, method in enumerate(methods):
        draw.text((left + j * cell_w + cell_w / 2, top - 32), method.upper(), font=font(22, True), fill=INK, anchor="ms")
    for i, product in enumerate(products):
        draw.text((left - 24, top + i * cell_h + cell_h / 2), SHORT[product], font=font(22, True), fill=INK, anchor="rm")
        values = results["forecast_detail"][product]["candidate_wape"]
        best = min(values, key=values.get)
        for j, method in enumerate(methods):
            value = values[method]
            intensity = value / max_wape
            base = (255, 255, 255)
            target = (255, 157, 102)
            rgb = tuple(round(base[k] + (target[k] - base[k]) * intensity) for k in range(3))
            fill = "#%02x%02x%02x" % rgb
            x1, y1 = left + j * cell_w, top + i * cell_h
            outline = GREEN if method == best else GRID
            width = 6 if method == best else 2
            draw.rounded_rectangle((x1 + 4, y1 + 4, x1 + cell_w - 6, y1 + cell_h - 6), radius=12, fill=fill, outline=outline, width=width)
            draw.text((x1 + cell_w / 2, y1 + cell_h / 2 - 8), f"{value:.1%}", font=font(27, True), fill=INK, anchor="mm")
            if method == best:
                draw.text((x1 + cell_w / 2, y1 + cell_h / 2 + 28), "SELECTED", font=font(15, True), fill=GREEN, anchor="mm")
    draw.text((left, 840), "Metric: weighted absolute percentage error (lower is better)", font=font(21), fill=MUTED)
    save(image, "07_forecast_model_comparison.png")


def draw_forecast_outlook(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Four-week demand outlook",
        "The selected forecast is shown with an empirical 80% error interval for capacity planning.",
        size=(1600, 1280),
    )
    history: dict[str, list[int]] = defaultdict(list)
    for row in results["weekly_history"]:
        history[row["product"]].append(row["count"])
    products = sorted(history)
    left, right = 330, 1440
    panel_h = 174
    start_y = 230
    for index, product in enumerate(products):
        y_top = start_y + index * panel_h
        y_bottom = y_top + 122
        observed = history[product][-12:]
        detail = results["forecast_detail"][product]
        point, lower, upper = detail["point"], detail["lower"], detail["upper"]
        values = observed + point + upper + lower
        y_max = max(values) + 3
        y_min = max(0, min(values) - 3)
        draw.line((left, y_bottom, right, y_bottom), fill=GRID, width=2)
        split_x = left + (right - left) * 11 / 15
        draw.rectangle((split_x, y_top, right, y_bottom), fill="#E9F1EE")
        draw.line((split_x, y_top, split_x, y_bottom), fill=GREEN, width=3)

        def point_xy(i: int, value: float) -> tuple[float, float]:
            x = left + (right - left) * i / 15
            y = y_bottom - (y_bottom - y_top) * (value - y_min) / max(1, y_max - y_min)
            return x, y

        observed_points = [point_xy(i, value) for i, value in enumerate(observed)]
        forecast_points = [point_xy(11 + i, value) for i, value in enumerate([observed[-1]] + point)]
        upper_points = [point_xy(12 + i, value) for i, value in enumerate(upper)]
        lower_points = [point_xy(12 + i, value) for i, value in enumerate(lower)]
        polygon = upper_points + list(reversed(lower_points))
        draw.polygon(polygon, fill="#B7D2C9")
        draw.line(observed_points, fill=MUTED, width=4)
        draw.line(forecast_points, fill=GREEN, width=6)
        for x, y in forecast_points[1:]:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=LIME, outline=GREEN, width=2)
        draw.text((left - 24, (y_top + y_bottom) / 2), SHORT[product], font=font(21, True), fill=INK, anchor="rm")
        draw.text((right + 4, y_top + 20), f"{detail['method'].upper()}  |  WAPE {detail['backtest_wape']:.1%}", font=font(17, True), fill=GREEN, anchor="rs")
    draw.text((left, 1130), "Observed", font=font(20, True), fill=MUTED)
    draw.line((left + 105, 1143, left + 155, 1143), fill=MUTED, width=5)
    draw.text((left + 220, 1130), "Forecast", font=font(20, True), fill=GREEN)
    draw.line((left + 325, 1143, left + 375, 1143), fill=GREEN, width=6)
    draw.rectangle((left + 485, 1129, left + 535, 1156), fill="#B7D2C9")
    draw.text((left + 550, 1130), "80% interval", font=font(20, True), fill=INK)
    save(image, "08_four_week_forecast_outlook.png")


def draw_workforce_capacity(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Workforce capacity by queue",
        "Recommended headcount covers the peak 80% upper bound under dedicated-team assumptions.",
    )
    teams = results["staffing"]["teams"]
    left, top, right, bottom = 430, 255, 1470, 830
    max_value = max(team["weekly_capacity"] for team in teams)
    for tick in range(0, max_value + 1, 12):
        x = left + (right - left) * tick / max_value
        draw.line((x, top, x, bottom), fill=GRID, width=2)
        axis_label(draw, (x, bottom + 30), str(tick))
    row_h = (bottom - top) / len(teams)
    for index, team in enumerate(teams):
        y = top + index * row_h + 14
        draw.text((left - 22, y + 35), SHORT[team["team"]], font=font(22, True), fill=INK, anchor="rm")
        capacity_w = (right - left) * team["weekly_capacity"] / max_value
        planning_w = (right - left) * team["planning_demand"] / max_value
        point_w = (right - left) * team["peak_weekly_demand"] / max_value
        draw.rounded_rectangle((left, y, left + capacity_w, y + 69), radius=12, fill="#DDEBE6")
        draw.rounded_rectangle((left, y + 10, left + planning_w, y + 59), radius=10, fill=GREEN_2)
        draw.line((left + point_w, y + 4, left + point_w, y + 65), fill=LIME, width=6)
        draw.text((left + capacity_w + 14, y + 34), f"{team['recommended_agents']} agent{'s' if team['recommended_agents'] != 1 else ''}", font=font(20, True), fill=INK, anchor="lm")
    legend = [("Capacity", "#DDEBE6"), ("Planning demand", GREEN_2), ("Point peak", LIME)]
    for index, (label, color) in enumerate(legend):
        x = 510 + index * 285
        draw.rounded_rectangle((x, 205, x + 38, 229), radius=5, fill=color)
        draw.text((x + 50, 217), label, font=font(19, True), fill=INK, anchor="lm")
    assumptions = results["staffing"]["assumptions"]
    draw.text((left, 885), f"Base plan: {results['staffing']['total_agents']} agents  |  ${results['staffing']['weekly_cost']:,}/week  |  {assumptions['cases_per_agent_week']} cases per agent-week", font=font(22, True), fill=GREEN)
    save(image, "09_workforce_capacity.png")


def draw_scenario_sensitivity(results: dict[str, object]) -> None:
    image, draw = chart_base(
        "Demand-stress sensitivity",
        "Discrete headcount steps show where a modest volume shock creates a real capacity decision.",
    )
    teams = results["staffing"]["teams"]
    productivity = results["staffing"]["assumptions"]["cases_per_agent_week"]
    weekly_cost = results["staffing"]["assumptions"]["weekly_cost_per_agent"]
    stress_values = list(range(0, 41, 5))
    agents = [
        sum(math.ceil(team["planning_demand"] * (1 + stress / 100) / productivity) for team in teams)
        for stress in stress_values
    ]
    costs = [value * weekly_cost for value in agents]
    left, top, right, bottom = 150, 280, 1450, 825
    min_agents, max_agents = min(agents) - 1, max(agents) + 1
    for tick in range(min_agents, max_agents + 1):
        y = bottom - (bottom - top) * (tick - min_agents) / (max_agents - min_agents)
        draw.line((left, y, right, y), fill=GRID, width=2)
        axis_label(draw, (left - 25, y), str(tick), anchor="rm")
    points = []
    for i, (stress, value) in enumerate(zip(stress_values, agents)):
        x = left + (right - left) * i / (len(stress_values) - 1)
        y = bottom - (bottom - top) * (value - min_agents) / (max_agents - min_agents)
        points.append((x, y))
        axis_label(draw, (x, bottom + 36), f"+{stress}%")
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=GREEN, outline=WHITE, width=3)
        draw.text((x, y - 22), str(value), font=font(20, True), fill=INK, anchor="ms")
    draw.line(points, fill=GREEN, width=7, joint="curve")
    draw.text((left, 220), "Total agents", font=font(24, True), fill=GREEN)
    draw.text((right, 220), "Weekly cost at each step", font=font(24, True), fill=INK, anchor="rs")
    previous = None
    for i, (stress, value, cost) in enumerate(zip(stress_values, agents, costs)):
        if value != previous:
            x, y = points[i]
            box_x = min(right - 200, max(left, x - 95))
            box_y = min(bottom - 15, y + 34)
            draw.rounded_rectangle((box_x, box_y, box_x + 190, box_y + 52), radius=10, fill=WHITE, outline=GRID, width=2)
            draw.text((box_x + 95, box_y + 26), f"${cost:,}/week", font=font(18, True), fill=INK, anchor="mm")
        previous = value
    draw.text((left, 885), "Stress is applied to each queue's planning demand before rounding up dedicated-team headcount.", font=font(21), fill=MUTED)
    save(image, "10_demand_stress_sensitivity.png")


def main() -> None:
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    model_analysis = build_model_analysis()
    draw_product_mix(results)
    draw_weekly_trends(results)
    draw_split_timeline(model_analysis)
    draw_confusion_matrix(model_analysis)
    draw_class_performance(model_analysis)
    draw_threshold_tradeoff(results)
    draw_forecast_comparison(results)
    draw_forecast_outlook(results)
    draw_workforce_capacity(results)
    draw_scenario_sensitivity(results)
    metrics = {
        "artifact_version": 1,
        "mode": "synthetic-sample",
        **model_analysis,
        "charts": sorted(path.name for path in PLOTS.glob("*.png")),
    }
    (ROOT / "reports" / "visualization_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(metrics['charts'])} charts in {PLOTS}")


if __name__ == "__main__":
    main()
