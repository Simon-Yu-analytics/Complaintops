# Analysis output contract

`results.json` is the machine-readable output produced by
`python -m complaintops.pipeline`. The dashboard consumes an identical copy at
`dashboard/data/results.json`.

## Top-level sections

| Key | Contents |
|---|---|
| `mode` | identifies the synthetic demonstration run |
| `records`, `date_range` | dataset scope |
| `classification` | overall scores, split sizes, cutoffs, calibration policy, and frozen-test routing results |
| `product_counts`, `top_issues` | descriptive operating mix |
| `weekly_history` | observed weekly product volumes used by the dashboard |
| `forecast_detail` | selected method, every candidate WAPE, point forecast, and 80% interval by product |
| `staffing` | productivity/cost assumptions, upper-bound demand, agents, capacity, and point-forecast utilization |

Numeric metrics are rounded when the report is written. The pipeline writes the
report only after schema validation, temporal evaluation, forecasting, and
staffing calculations complete successfully.
