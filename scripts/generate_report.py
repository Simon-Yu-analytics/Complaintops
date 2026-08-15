from __future__ import annotations

import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "plots"
OUTPUT = ROOT / "reports" / "ComplaintOps_Analysis_Report.pdf"
RESULTS = json.loads((ROOT / "dashboard" / "data" / "results.json").read_text(encoding="utf-8"))
METRICS = json.loads((ROOT / "reports" / "visualization_metrics.json").read_text(encoding="utf-8"))

WIDTH, HEIGHT = letter
MARGIN = 46
INK = colors.HexColor("#171B1A")
MUTED = colors.HexColor("#65706C")
PAPER = colors.HexColor("#F4F6F3")
WHITE = colors.white
GREEN = colors.HexColor("#16483B")
GREEN_2 = colors.HexColor("#2F735E")
LIME = colors.HexColor("#D7FF45")
ORANGE = colors.HexColor("#FF9D66")
BLUE = colors.HexColor("#5D8FE8")
GRID = colors.HexColor("#DDE3DF")


def register_fonts() -> None:
    regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ReportRegular", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportBold", str(bold)))
    else:
        pdfmetrics.registerFont(TTFont("ReportRegular", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("ReportBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))


def split_lines(text: str, width: float, font_name: str, font_size: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and pdfmetrics.stringWidth(trial, font_name, font_size) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def paragraph(c: canvas.Canvas, text: str, x: float, y: float, width: float, *, size: float = 10.2, leading: float = 14, color=MUTED, bold: bool = False) -> float:
    name = "ReportBold" if bold else "ReportRegular"
    c.setFont(name, size)
    c.setFillColor(color)
    for line in split_lines(text, width, name, size):
        c.drawString(x, y, line)
        y -= leading
    return y


def section_header(c: canvas.Canvas, section: str, title: str, page: int) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.rect(0, 0, 8, HEIGHT, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("ReportBold", 8.5)
    c.drawString(MARGIN, HEIGHT - 35, section.upper())
    c.setFillColor(INK)
    c.setFont("ReportBold", 24)
    c.drawString(MARGIN, HEIGHT - 68, title)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.8)
    c.line(MARGIN, HEIGHT - 82, WIDTH - MARGIN, HEIGHT - 82)
    footer(c, page)


def footer(c: canvas.Canvas, page: int) -> None:
    c.setFillColor(MUTED)
    c.setFont("ReportRegular", 7.7)
    c.drawString(MARGIN, 24, "ComplaintOps | Synthetic demonstration data; not production performance")
    c.drawRightString(WIDTH - MARGIN, 24, f"{page:02d}")


def draw_image(c: canvas.Canvas, filename: str, x: float, y: float, width: float, height: float) -> None:
    image_path = PLOTS / filename
    image = ImageReader(str(image_path))
    source_w, source_h = image.getSize()
    scale = min(width / source_w, height / source_h)
    draw_w, draw_h = source_w * scale, source_h * scale
    c.drawImage(image, x + (width - draw_w) / 2, y + (height - draw_h) / 2, draw_w, draw_h, preserveAspectRatio=True, mask="auto")


def insight_box(c: canvas.Canvas, title: str, body: str, y: float, *, accent=GREEN) -> None:
    box_h = 78
    c.setFillColor(WHITE)
    c.setStrokeColor(GRID)
    c.roundRect(MARGIN, y, WIDTH - 2 * MARGIN, box_h, 10, fill=1, stroke=1)
    c.setFillColor(accent)
    c.roundRect(MARGIN + 12, y + 15, 5, box_h - 30, 2, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("ReportBold", 10.5)
    c.drawString(MARGIN + 28, y + box_h - 25, title)
    paragraph(c, body, MARGIN + 28, y + box_h - 43, WIDTH - 2 * MARGIN - 52, size=9.2, leading=12, color=MUTED)


def stat_card(c: canvas.Canvas, x: float, y: float, w: float, value: str, label: str, *, accent=GREEN) -> None:
    c.setFillColor(WHITE)
    c.setStrokeColor(GRID)
    c.roundRect(x, y, w, 84, 10, fill=1, stroke=1)
    c.setFillColor(accent)
    c.setFont("ReportBold", 22)
    c.drawString(x + 14, y + 48, value)
    c.setFillColor(MUTED)
    c.setFont("ReportRegular", 8.8)
    c.drawString(x + 14, y + 22, label)


def cover(c: canvas.Canvas) -> None:
    c.setFillColor(GREEN)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.rect(0, 0, 13, HEIGHT, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.setFont("ReportBold", 10)
    c.drawString(54, 716, "BUSINESS ANALYTICS PORTFOLIO CASE STUDY")
    c.setFillColor(WHITE)
    c.setFont("ReportBold", 38)
    c.drawString(54, 638, "ComplaintOps")
    c.setFont("ReportBold", 23)
    c.drawString(54, 596, "From customer voice to operating decisions")
    paragraph(
        c,
        "A reproducible analysis of confidence-aware complaint routing, queue forecasting, workforce capacity, and customer support design.",
        54,
        554,
        455,
        size=13.5,
        leading=19,
        color=colors.HexColor("#D8E4DF"),
    )
    metrics = [
        ("6,165", "synthetic complaints"),
        ("81.8%", "routing accuracy"),
        ("9.3%", "average forecast WAPE"),
        ("9", "base-plan agents"),
    ]
    for index, (value, label) in enumerate(metrics):
        x = 54 + (index % 2) * 250
        y = 380 - (index // 2) * 96
        c.setFillColor(colors.HexColor("#245A4C"))
        c.roundRect(x, y, 222, 72, 11, fill=1, stroke=0)
        c.setFillColor(LIME)
        c.setFont("ReportBold", 20)
        c.drawString(x + 16, y + 39, value)
        c.setFillColor(WHITE)
        c.setFont("ReportRegular", 9)
        c.drawString(x + 16, y + 18, label)
    c.setFillColor(WHITE)
    c.setFont("ReportBold", 11)
    c.drawString(54, 125, "Junhui (Simon) Yu")
    c.setFont("ReportRegular", 9.5)
    c.drawString(54, 106, "Economics: Data Science | University of Washington")
    c.drawString(54, 88, "August 2026 | Version 1.1")
    c.setFillColor(colors.HexColor("#AFC4BC"))
    c.setFont("ReportRegular", 7.8)
    c.drawString(54, 43, "Synthetic-data case study. Results demonstrate the workflow, not a live financial service.")


def executive_summary(c: canvas.Canvas, page: int) -> None:
    section_header(c, "Executive summary", "What the project demonstrates", page)
    paragraph(
        c,
        "ComplaintOps connects three decisions that are often separated in portfolio work: where a complaint should go, how much work each queue should expect, and how much capacity should be scheduled. A customer-facing prototype adds explanation, human review, and feedback without pretending the demo is a live service.",
        MARGIN,
        680,
        WIDTH - 2 * MARGIN,
        size=10.8,
        leading=15,
        color=INK,
    )
    cards = [
        ("81.8%", "overall routing accuracy", GREEN),
        ("80.4%", "macro-F1", BLUE),
        ("86.5%", "auto-route accuracy", GREEN_2),
        ("15.9%", "sent to human review", ORANGE),
        ("9.3%", "average forecast WAPE", BLUE),
        ("$14,850", "base weekly staffing cost", GREEN),
    ]
    card_w = (WIDTH - 2 * MARGIN - 20) / 3
    for index, (value, label, accent) in enumerate(cards):
        x = MARGIN + (index % 3) * (card_w + 10)
        y = 480 - (index // 3) * 100
        stat_card(c, x, y, card_w, value, label, accent=accent)
    c.setFillColor(GREEN)
    c.roundRect(MARGIN, 250, WIDTH - 2 * MARGIN, 92, 12, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.setFont("ReportBold", 12)
    c.drawString(MARGIN + 20, 316, "CORE BUSINESS INTERPRETATION")
    paragraph(
        c,
        "The model should not force every case into automation. A calibration-selected threshold routes 84.1% of final test cases automatically at 86.5% accuracy and reserves the remaining 15.9% for review. Forecast uncertainty then flows into an explicit nine-agent capacity plan.",
        MARGIN + 20,
        292,
        WIDTH - 2 * MARGIN - 40,
        size=10,
        leading=14,
        color=WHITE,
    )
    insight_box(
        c,
        "Scope boundary",
        "Every metric in this report comes from a deterministic synthetic dataset. The purpose is to demonstrate analytical reasoning, validation, and product design - not to claim production performance or customer impact.",
        112,
        accent=ORANGE,
    )


def workflow(c: canvas.Canvas, page: int) -> None:
    section_header(c, "Decision design", "One analysis, four connected decisions", page)
    paragraph(
        c,
        "The project is structured as a decision pipeline. Each output becomes an input to the next stage, so the analysis ends with an operating recommendation rather than a collection of unrelated charts.",
        MARGIN,
        682,
        WIDTH - 2 * MARGIN,
        size=10.5,
        leading=14,
        color=INK,
    )
    steps = [
        ("1", "INTAKE", "Customer narrative", "Capture a complaint and explain the privacy boundary."),
        ("2", "ROUTE", "Predicted queue", "Rank queue scores; uncertain cases move to review."),
        ("3", "FORECAST", "Four-week workload", "Select a simple method independently for each queue."),
        ("4", "STAFF", "Capacity plan", "Cover the highest 80% forecast upper bound."),
    ]
    box_w = 116
    for index, (number, label, title, body) in enumerate(steps):
        x = MARGIN + index * 130
        c.setFillColor(WHITE)
        c.setStrokeColor(GRID)
        c.roundRect(x, 390, box_w, 205, 12, fill=1, stroke=1)
        c.setFillColor(GREEN if index != 1 else ORANGE)
        c.circle(x + 24, 565, 13, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("ReportBold", 9)
        c.drawCentredString(x + 24, 562, number)
        c.setFillColor(MUTED)
        c.setFont("ReportBold", 7.5)
        c.drawString(x + 13, 528, label)
        c.setFillColor(INK)
        c.setFont("ReportBold", 11)
        for line_i, line in enumerate(split_lines(title, box_w - 26, "ReportBold", 11)):
            c.drawString(x + 13, 500 - line_i * 14, line)
        paragraph(c, body, x + 13, 451, box_w - 26, size=8.4, leading=11, color=MUTED)
        if index < len(steps) - 1:
            c.setStrokeColor(GREEN)
            c.setLineWidth(2)
            c.line(x + box_w + 4, 492, x + box_w + 12, 492)
            c.line(x + box_w + 8, 496, x + box_w + 12, 492)
            c.line(x + box_w + 8, 488, x + box_w + 12, 492)
    c.setFillColor(GREEN)
    c.roundRect(MARGIN, 235, WIDTH - 2 * MARGIN, 105, 12, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.setFont("ReportBold", 10)
    c.drawString(MARGIN + 18, 312, "CUSTOMER EXPERIENCE LAYER")
    paragraph(
        c,
        "The interactive application lets a user submit a sample narrative, view ranked routing scores, request a human specialist, open a device-local demo case, ask guided support questions, and leave a 1-5 rating with written feedback. No real complaint text is transmitted.",
        MARGIN + 18,
        287,
        WIDTH - 2 * MARGIN - 36,
        size=9.7,
        leading=13,
        color=WHITE,
    )
    insight_box(
        c,
        "Why this matters for business analytics",
        "The same model can be technically accurate yet operationally poor if it hides uncertainty, provides no escalation path, or turns forecast averages into false staffing precision. ComplaintOps makes those policy choices visible.",
        105,
    )


def visual_page(c: canvas.Canvas, page: int, section: str, title: str, filename: str, insight_title: str, insight_body: str, *, image_height: float = 510, accent=GREEN) -> None:
    section_header(c, section, title, page)
    draw_image(c, filename, MARGIN, 175, WIDTH - 2 * MARGIN, image_height)
    insight_box(c, insight_title, insight_body, 78, accent=accent)


def final_page(c: canvas.Canvas, page: int) -> None:
    section_header(c, "Conclusion", "Recommendations and reproducibility", page)
    c.setFillColor(GREEN)
    c.setFont("ReportBold", 12)
    c.drawString(MARGIN, 678, "DECISION RECOMMENDATIONS")
    recommendations = [
        "Keep the confidence-aware review path; do not optimize only for raw automation coverage.",
        "Benchmark every queue against the naive forecast before adopting a more complex method.",
        "Treat the nine-agent result as a transparent scenario, not a fixed staffing promise.",
        "Monitor class drift, review rate, forecast error, backlog age, and threshold stability together.",
    ]
    y = 647
    for index, item in enumerate(recommendations, 1):
        c.setFillColor(LIME)
        c.circle(MARGIN + 9, y + 2, 8, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("ReportBold", 8)
        c.drawCentredString(MARGIN + 9, y - 1, str(index))
        y = paragraph(c, item, MARGIN + 27, y + 5, WIDTH - 2 * MARGIN - 27, size=9.5, leading=12, color=INK) - 11
    c.setFillColor(ORANGE)
    c.setFont("ReportBold", 12)
    c.drawString(MARGIN, 480, "LIMITATIONS TO DEFEND IN AN INTERVIEW")
    limitations = [
        "Synthetic data cannot establish external validity or real customer impact.",
        "Naive Bayes confidence is a routing score, not a perfectly calibrated probability.",
        "Forecast WAPE is used for model selection and is not a separate untouched forecast holdout.",
        "Dedicated teams, fixed productivity, and no backlog or schedule constraints simplify workforce planning.",
        "The support assistant is rule-based and device-local; it is not a live customer-service channel.",
    ]
    y = 452
    for item in limitations:
        c.setFillColor(ORANGE)
        c.circle(MARGIN + 5, y + 3, 2.5, fill=1, stroke=0)
        y = paragraph(c, item, MARGIN + 15, y + 7, WIDTH - 2 * MARGIN - 15, size=9.1, leading=12, color=INK) - 6
    c.setFillColor(GREEN)
    c.roundRect(MARGIN, 150, WIDTH - 2 * MARGIN, 128, 12, fill=1, stroke=0)
    c.setFillColor(LIME)
    c.setFont("ReportBold", 10)
    c.drawString(MARGIN + 18, 250, "REPRODUCE THE SUBMISSION")
    c.setFillColor(WHITE)
    c.setFont("ReportRegular", 9.2)
    commands = [
        "make check",
        "python -m pip install -r requirements-viz.txt",
        "make visualizations",
        "make report",
    ]
    for index, command in enumerate(commands):
        c.drawString(MARGIN + 22, 225 - index * 19, f"$ {command}")
    c.setFillColor(MUTED)
    c.setFont("ReportRegular", 8)
    c.drawString(MARGIN, 108, "Repository: github.com/Simon-Yu-analytics/Complaintops")
    c.drawString(MARGIN, 91, "Author: Junhui (Simon) Yu | Economics: Data Science | University of Washington")


def build() -> None:
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=letter, pageCompression=1, invariant=1)
    c.setTitle("ComplaintOps Analysis Report")
    c.setAuthor("Junhui (Simon) Yu")
    c.setSubject("Business analytics portfolio case study")
    c.setKeywords("business analytics, complaint routing, forecasting, workforce planning")

    cover(c)
    c.showPage()
    executive_summary(c, 2)
    c.showPage()
    workflow(c, 3)
    c.showPage()
    visual_page(
        c, 4, "Data and methods", "Temporal validation without test leakage",
        "03_temporal_validation_design.png",
        "Validation rule",
        "The model learns from 3,673 older cases. A separate 935-case calibration window chooses the 0.9617 automation threshold. Only then is performance reported on 1,557 newer cases.",
        image_height=505,
    )
    c.showPage()
    visual_page(
        c, 5, "Complaint portfolio", "Where the workload is concentrated",
        "01_complaint_portfolio_mix.png",
        "Management readout",
        "Credit reporting contributes 1,892 cases, or 30.7% of the portfolio. Its scale makes even a small routing or forecast error operationally material; mortgage is smaller but still requires dedicated coverage under the current assumptions.",
        image_height=500,
    )
    c.showPage()
    visual_page(
        c, 6, "Complaint portfolio", "How weekly queue demand changes",
        "02_weekly_demand_trends.png",
        "Planning readout",
        "The five queues move at different levels and with different short-run patterns. Forecasting each queue independently is more defensible than applying one aggregate growth assumption to the entire operation.",
        image_height=500,
    )
    c.showPage()
    visual_page(
        c, 7, "Routing evaluation", "Where the classifier makes mistakes",
        "04_routing_confusion_matrix.png",
        "Error pattern",
        "Credit reporting has the strongest test recall at 85%. Mortgage is hardest at 76%, with the largest single error share moving to credit reporting. These off-diagonal cells identify where human-review guidance and targeted data collection should focus.",
        image_height=515,
        accent=ORANGE,
    )
    c.showPage()
    visual_page(
        c, 8, "Routing evaluation", "Balanced performance across queues",
        "05_class_performance.png",
        "Why macro-F1 is reported",
        "Overall accuracy can be dominated by the largest class. The 80.4% macro-F1 gives equal weight to all five queues and exposes the lower mortgage precision and F1 that a single accuracy figure would hide.",
        image_height=500,
    )
    c.showPage()
    visual_page(
        c, 9, "Routing policy", "Trading automation coverage for quality",
        "06_threshold_tradeoff.png",
        "Frozen policy result",
        "The calibration window selected 0.9617 as the highest-coverage threshold meeting the 85% routed-accuracy target. On the untouched test period, that policy auto-routes 84.1% of cases at 86.5% accuracy and reviews 15.9%.",
        image_height=500,
        accent=ORANGE,
    )
    c.showPage()
    visual_page(
        c, 10, "Demand forecasting", "Selecting a baseline by queue",
        "07_forecast_model_comparison.png",
        "Model-selection result",
        "The naive forecast wins four queues. Only credit card benefits from the four-week moving average, and the improvement is modest. This is evidence against adding complexity merely to make the project look more advanced.",
        image_height=500,
    )
    c.showPage()
    visual_page(
        c, 11, "Demand forecasting", "Four-week operating outlook",
        "08_four_week_forecast_outlook.png",
        "Decision use",
        "Point forecasts support daily visibility, but the capacity decision uses the empirical 80% upper bound. Credit reporting has the highest four-week point forecast at 39 cases per week and an upper bound of 43.",
        image_height=515,
    )
    c.showPage()
    visual_page(
        c, 12, "Workforce planning", "Capacity against uncertainty",
        "09_workforce_capacity.png",
        "Base-plan recommendation",
        "At 24 cases per agent-week and $1,650 per agent-week, the dedicated-team scenario requires nine agents and $14,850 weekly. Visible slack is a consequence of integer headcount and queue separation, not hidden efficiency.",
        image_height=500,
    )
    c.showPage()
    visual_page(
        c, 13, "Scenario analysis", "When volume stress changes headcount",
        "10_demand_stress_sensitivity.png",
        "Sensitivity result",
        "The plan stays at nine agents through a 10% demand stress, rises to ten at 15%, and rises to eleven at 30%. The step pattern is important: small forecast changes do not always imply a real staffing action.",
        image_height=500,
        accent=ORANGE,
    )
    c.showPage()
    final_page(c, 14)
    c.save()
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
