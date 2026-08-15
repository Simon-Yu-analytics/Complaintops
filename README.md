# ComplaintOps

[![Offline quality gates](https://github.com/Simon-Yu-analytics/Complaintops/actions/workflows/ci.yml/badge.svg)](https://github.com/Simon-Yu-analytics/Complaintops/actions/workflows/ci.yml)

**Confidence-aware complaint routing, queue forecasting, and workforce scenario
planning for consumer-finance operations.**

ComplaintOps is a student-built analytics case study modeled around the work of
a customer-operations team. I built it to connect three questions that are
often analyzed separately:

1. Which product queue should receive a new complaint?
2. How many cases should each queue expect over the next four weeks?
3. How much dedicated capacity is required under normal and stressed demand?

The repository includes a privacy-safe offline dataset generator, a bounded CFPB
downloader, time-aware model validation, walk-forward forecast selection,
upper-bound capacity planning, 14 unit tests, CI, and a responsive four-view
decision dashboard.

## Contents

- [Why I built this](#why-i-built-this)
- [Decision workflow](#decision-workflow)
- [Demonstration snapshot](#demonstration-snapshot)
- [Technical decisions](#technical-decisions)
- [What is implemented](#what-is-implemented)
- [Reproduce the project](#reproduce-the-project)
- [Dashboard views](#dashboard-views)
- [Data source and responsible use](#data-source-and-responsible-use)
- [Assumptions and limitations](#assumptions-and-limitations)
- [What I learned](#what-i-learned)
- [Responsible next steps](#responsible-next-steps)

## Why I built this

Many portfolio projects stop after reporting complaint counts or model
accuracy. I wanted to practice the harder business-analytics step: deciding what
an operations team should do with the result. ComplaintOps therefore starts
with text routing, carries the predicted workload into a four-week forecast,
and ends with a capacity recommendation whose assumptions can be challenged.

I intentionally used understandable baseline methods instead of presenting a
complex model I could not defend in an interview. The focus is on validation,
trade-offs, and decision design rather than claiming production readiness.

## Decision workflow

```text
Narratives + dates
       |
       v
Schema checks --> temporal train/calibration/test split
       |                         |
       |                         +--> confidence-aware product routing
       |
       +--> weekly queues --> walk-forward model selection --> 80% interval
                                                            |
                                                            v
                                             capacity plan + stress scenario
                                                            |
                                                            v
                                                   decision dashboard
```

## Demonstration snapshot

The committed dashboard output is generated from **6,165 synthetic complaints**
covering 52 weeks. These are software-demonstration metrics, not claims about a
real financial institution.

| Decision metric | Result | How it is validated |
|---|---:|---|
| Overall routing accuracy | 81.8% | Newest 25% temporal holdout |
| Macro-F1 | 80.4% | Newest 25% temporal holdout |
| Auto-route accuracy | 86.5% | Unseen test cases above a calibration-selected threshold |
| Auto-route coverage | 84.1% | Remaining 15.9% sent to human review |
| Average forecast WAPE | 9.3% | Walk-forward backtest across five product queues |
| Base capacity plan | 9 agents | Dedicated teams staffed to each 80% forecast upper bound |

The confidence threshold is selected only on the middle calibration window to
target at least 85% routing accuracy. It is then frozen before evaluation on the
newest test period. This avoids selecting the threshold on the reported test
results.

The chronological evaluation contains 3,673 training cases, 935 calibration
cases, and 1,557 final test cases. The calibration window begins on 16 August
2025 and the untouched test window begins on 11 October 2025.

## Technical decisions

| Decision | Implementation | Reason |
|---|---|---|
| Routing model | Multinomial Naive Bayes | Fast, inspectable baseline that can be explained without hiding behind a framework |
| Validation | Chronological train/calibration/test | Reproduces the real operating constraint: future complaints are not available during training |
| Automation policy | Calibrated confidence threshold | Separates model quality from the business decision about which cases are safe to automate |
| Forecast selection | Per-queue walk-forward WAPE | Prevents one method from being assumed best for products with different demand patterns |
| Capacity risk | Highest 80% forecast upper bound | Makes the staffing recommendation reflect forecast uncertainty rather than only an average |

The routing model's intended use, evaluation design, failure modes, and
monitoring recommendations are documented in the [model card](docs/MODEL_CARD.md).

## What is implemented

### 1. Intake routing

- Inspectable multinomial Naive Bayes baseline implemented with the Python
  standard library.
- Chronological train, calibration, and test windows.
- Accuracy and macro-F1 for overall quality.
- A selective-routing policy that sends low-confidence predictions to a review
  queue instead of forcing every case through automation.
- Calibration policy, threshold, coverage, review rate, and test cutoff exposed
  in the machine-readable report.

### 2. Queue forecasting

- Weekly product-level aggregation with missing weeks represented as zeros.
- Fair walk-forward comparison of last-value, four-week average, eight-week
  average, and eight-week local-trend baselines.
- Lowest-WAPE method selected independently for each product queue.
- Four-week point forecasts and empirical 80% error intervals.
- Naive benchmark retained in the output so model complexity is only used when
  it improves the backtest.

### 3. Workforce planning

- Staffing is based on the highest 80% forecast upper bound, not only the point
  estimate.
- Explicit productivity assumption of 24 closed cases per agent per week.
- Explicit weekly fully loaded cost assumption of $1,650 per agent.
- Dedicated product-team assumption disclosed rather than hidden.
- Interactive 0%–40% demand stress control recalculates agents, capacity,
  utilization, and cost in the browser.

## Reproduce the project

The offline project has no third-party Python dependencies.

```bash
git clone https://github.com/Simon-Yu-analytics/Complaintops.git
cd Complaintops
make verify
make dashboard
```

Open `http://localhost:8000`. `make verify` runs all 14 tests, regenerates the
synthetic dataset, rebuilds both JSON outputs, and byte-compiles the code.

Useful individual commands:

```bash
make sample   # deterministically recreate data/sample/complaints.csv
make test     # run the 14-test standard-library suite
make run      # regenerate data and rebuild reports/dashboard output
```

## Dashboard views

- **Overview:** portfolio mix, operating KPIs, forecast error, and management
  readout.
- **Triage intelligence:** overall scorecard, frozen test cutoff, confidence
  threshold, automation coverage, and review rate.
- **Demand forecast:** selected method and WAPE for every product plus point and
  80% interval bars.
- **Workforce plan:** upper-bound capacity by queue and an interactive demand
  stress scenario.

## Repository layout

```text
Complaintops/
├── .github/workflows/ci.yml       CI quality gate
├── dashboard/                     four-view HTML/CSS/JS decision console
│   └── data/results.json          committed render-ready output
├── data/
│   ├── README.md                  data policy
│   └── sample/                    locally generated CSV (Git-ignored)
├── docs/MODEL_CARD.md             intended use, evaluation, and risks
├── reports/
│   ├── README.md                  output contract
│   └── results.json               machine-readable analysis output
├── scripts/generate_sample.py     deterministic data generator
├── src/complaintops/              routing, forecast, and capacity modules
├── tests/test_core.py             unit and policy tests
├── LICENSE
├── Makefile
└── README.md
```

## Data source and responsible use

The production extension is designed for the [CFPB Consumer Complaint
Database](https://www.consumerfinance.gov/data-research/consumer-complaints/).
CFPB explains that published complaints are not a statistical sample of every
consumer experience. Raw complaint counts therefore should not be treated as a
company-quality ranking without exposure or market-share denominators.

This project deliberately avoids a “worst bank” leaderboard. The generated
sample contains no consumer text or personal information. Real extracts belong
in the Git-ignored `data/raw/` directory and should be reviewed under the CFPB
data-use notice before analysis.

## Assumptions and limitations

- Synthetic benchmark results demonstrate the pipeline, not production model
  performance.
- Naive Bayes confidence is a routing score, not a perfectly calibrated
  probability; the policy must be monitored and recalibrated on real data.
- Forecast intervals use historical absolute errors and do not model correlated
  shocks, holidays, regulatory events, or structural breaks.
- Forecast WAPE is the rolling-origin selection score, not a separate final
  holdout estimate; it can be optimistic after choosing the lowest-error method.
- The staffing model assumes dedicated product teams and a fixed productivity
  rate. Cross-trained agents, schedules, backlog age, shrinkage, and queueing
  service levels would be required for production workforce management.
- The public downloader is bounded for reproducible exploration; a production
  ingestion job would add pagination, versioned snapshots, retention controls,
  and data-quality alerts.

## What I learned

- Accuracy alone is incomplete: an automation policy also needs coverage and a
  clear path for uncertain cases.
- A simple forecast can outperform a more complicated one, so every product
  queue should be compared with a naive benchmark.
- Workforce recommendations are driven as much by productivity and risk
  assumptions as by the forecast itself.
- Synthetic data is useful for reproducible engineering, but it must be labeled
  clearly and cannot substitute for an external-data benchmark.

## Responsible next steps

- Benchmark against a versioned public CFPB extract using the same temporal
  evaluation design.
- Add TF-IDF logistic regression as a challenger without replacing the
  interpretable baseline by default.
- Monitor class drift, review rate, routing accuracy, and threshold stability.
- Extend capacity planning with backlog age and Erlang/queue simulation only
  after the required service-level inputs are available.

## Author

**Junhui (Simon) Yu** — Economics: Data Science, University of Washington

Released under the [MIT License](LICENSE).
