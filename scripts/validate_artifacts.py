from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "plots"
REPORT = ROOT / "reports" / "ComplaintOps_Analysis_Report.pdf"
EXPECTED_CHARTS = {
    "01_complaint_portfolio_mix.png",
    "02_weekly_demand_trends.png",
    "03_temporal_validation_design.png",
    "04_routing_confusion_matrix.png",
    "05_class_performance.png",
    "06_threshold_tradeoff.png",
    "07_forecast_model_comparison.png",
    "08_four_week_forecast_outlook.png",
    "09_workforce_capacity.png",
    "10_demand_stress_sensitivity.png",
}


def main() -> None:
    actual = {path.name for path in PLOTS.glob("*.png")}
    if actual != EXPECTED_CHARTS:
        raise AssertionError(f"chart set mismatch: {sorted(actual ^ EXPECTED_CHARTS)}")
    for path in sorted(PLOTS.glob("*.png")):
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 1500 or image.height < 950:
                raise AssertionError(f"chart resolution too small: {path.name} {image.size}")
    metrics = json.loads((ROOT / "reports" / "visualization_metrics.json").read_text(encoding="utf-8"))
    if metrics["mode"] != "synthetic-sample" or metrics["charts"] != sorted(EXPECTED_CHARTS):
        raise AssertionError("visualization metrics do not match the chart contract")
    reader = PdfReader(str(REPORT))
    if len(reader.pages) != 14:
        raise AssertionError(f"expected 14 report pages, found {len(reader.pages)}")
    if reader.metadata.title != "ComplaintOps Analysis Report":
        raise AssertionError("report title metadata is missing")
    for index, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if len(text.strip()) < 80:
            raise AssertionError(f"report page {index} has too little extractable text")
        if "Synthetic" not in text:
            raise AssertionError(f"report page {index} is missing the synthetic-data disclosure")
    if REPORT.stat().st_size < 100_000:
        raise AssertionError("report file is unexpectedly small")
    print("Validated 10 PNG charts and a 14-page analysis report")


if __name__ == "__main__":
    main()
