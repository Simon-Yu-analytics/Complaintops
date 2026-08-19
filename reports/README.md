# Analysis output contract

`results.json` is the machine-readable output produced by
`python -m complaintops.pipeline`. The dashboard consumes an identical copy at
`dashboard/data/results.json`. It also exports the fitted synthetic model to
`dashboard/data/model.json` and combines both artifacts in
`dashboard/data/app-data.js` so the application can run without a backend.

## Top-level sections

| Key | Contents |
|---|---|
| `mode` | identifies the synthetic demonstration run |
| `records`, `date_range` | dataset scope |
| `classification` | overall scores, split sizes, cutoffs, calibration policy/curve, and frozen-test routing results |
| `product_counts`, `top_issues` | descriptive operating mix |
| `weekly_history` | observed weekly product volumes used by the dashboard |
| `forecast_detail` | selected method, every candidate WAPE, point forecast, and 80% interval by product |
| `staffing` | productivity/cost assumptions, upper-bound demand, agents, capacity, and point-forecast utilization |

Numeric metrics are rounded when the report is written. The pipeline writes the
report only after schema validation, temporal evaluation, forecasting, and
staffing calculations complete successfully.

## Human-readable report

`ComplaintOps_Analysis_Report.pdf` is a 14-page portfolio report that turns the
machine-readable output into a visual business narrative. It covers portfolio
mix, chronological validation, routing errors, class-level quality, the
automation threshold, forecast selection, four-week uncertainty, base capacity,
and demand-stress sensitivity. Every page identifies the results as synthetic
demonstration data.

`visualization_metrics.json` stores the test-set confusion matrix and class-level
scores used by the visualization script. Rebuild and validate the complete
project artifacts with `make artifacts` after installing `requirements-viz.txt`.
