# Visualization gallery

These figures are generated from the committed synthetic demonstration pipeline.
They are decision-oriented rather than decorative: each chart answers a routing,
forecasting, or capacity-planning question.

| File | Decision question |
|---|---|
| `01_complaint_portfolio_mix.png` | Which queues carry the most volume? |
| `02_weekly_demand_trends.png` | How does weekly demand vary by queue? |
| `03_temporal_validation_design.png` | How are training, calibration, and final testing separated? |
| `04_routing_confusion_matrix.png` | Which product queues are confused on future cases? |
| `05_class_performance.png` | Is model quality balanced across queues? |
| `06_threshold_tradeoff.png` | What accuracy/coverage trade-off sets the review policy? |
| `07_forecast_model_comparison.png` | Which simple forecast wins for each queue? |
| `08_four_week_forecast_outlook.png` | What volume and uncertainty should operations plan for? |
| `09_workforce_capacity.png` | Does recommended capacity cover the planning demand? |
| `10_demand_stress_sensitivity.png` | When does a demand shock require more headcount? |

Rebuild the gallery with `make visualizations` after installing the optional
packages in `requirements-viz.txt`.
