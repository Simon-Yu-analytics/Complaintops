# ComplaintOps

**NLP complaint triage, queue forecasting, and SLA-aware workforce planning for consumer finance operations.**

ComplaintOps is a decision system for a Head of Customer Operations or Compliance. It connects three questions that are often analyzed separately:

1. Where should a newly received complaint be routed?
2. How many cases will each product team receive next month?
3. How many analysts are required to protect the service-level target?

The repository ships with a privacy-safe offline mode, an interactive four-page dashboard, tests, and a bounded downloader for the public CFPB Consumer Complaint Database.

## Decision workflow

```text
Narratives + dates
       |
       v
Schema validation --> NLP product routing --> weekly queue forecast
                                                |
                                                v
                                  SLA-buffered staffing plan
                                                |
                                                v
                                      Decision dashboard
```

## What is implemented

- Inspectable multinomial Naive Bayes text baseline
- Stratified holdout accuracy and macro-F1 evaluation
- Weekly product-queue aggregation
- Rolling moving-average forecast with historical WAPE
- Capacity model with productivity, cost, and SLA-buffer assumptions
- Responsive dashboard with Overview, Triage, Forecast, and Workforce pages
- Deterministic sample-data generator and standard-library test suite
- GitHub Actions quality gate

## Quick start

```bash
git clone https://github.com/simon-yu-analytics/complaintops.git
cd complaintops
make test
make run
make dashboard
```

Open `http://localhost:8000` after starting the dashboard.

## Repository layout

```text
complaintops/
├── .github/workflows/ci.yml
├── dashboard/
│   ├── data/results.json
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── data/sample/
├── reports/
├── scripts/generate_sample.py
├── src/complaintops/
├── tests/
├── Makefile
└── README.md
```

## Data source and responsible use

The production pipeline is designed for the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/). CFPB states that the database is not a statistical sample of all consumer experiences, and raw complaint counts should not be interpreted as company quality without exposure or market-share denominators.

For that reason, this project does **not** publish a “worst bank” ranking. It uses complaint records as an operations corpus for routing, workload forecasting, and capacity planning. The generated sample is synthetic and contains no consumer text.

## Model governance

- Predictions below an operating confidence threshold should go to human review.
- Product taxonomy changes require monitoring and retraining.
- Forecasts are planning signals, not promises; uncertainty and event shocks matter.
- Staffing recommendations depend on explicit productivity and service-buffer assumptions.
- Sample-mode metrics demonstrate software integration only and are never presented as production evidence.

## Roadmap

- [x] Privacy-safe offline pipeline
- [x] Routing, forecasting, staffing, and dashboard integration
- [x] Automated tests
- [ ] Full CFPB benchmark with time-based validation
- [ ] TF-IDF logistic-regression challenger
- [ ] Prediction confidence monitoring
- [ ] Scenario controls in the workforce dashboard

## Author

Junhui (Simon) Yu — Economics: Data Science, University of Washington
