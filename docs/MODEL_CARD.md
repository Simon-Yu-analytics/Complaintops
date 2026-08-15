# Routing model card

## Model overview

ComplaintOps uses a standard-library implementation of multinomial Naive Bayes
to route complaint narratives into five product queues. The model is an
interpretable baseline for an operations case study, not a production decision
system.

## Intended use

- Suggest a product queue for newly received English-language complaints.
- Auto-route only cases above a threshold selected on a calibration period.
- Send all lower-confidence cases to a human review queue.

The model should not determine complaint validity, customer eligibility,
compensation, regulatory reporting, or any other outcome affecting a consumer.

## Evaluation design

The 6,165-record synthetic dataset is ordered by `date_received` and divided
into three non-overlapping windows:

| Window | Records | Role |
|---|---:|---|
| Training | 3,673 | Estimate vocabulary, priors, and token likelihoods |
| Calibration | 935 | Choose the automation threshold for an 85% accuracy target |
| Test | 1,557 | Report final quality after all policy choices are frozen |

On the test window, overall accuracy is 81.8% and macro-F1 is 80.4%. At the
frozen 0.9617 threshold, 84.1% of cases are auto-routed at 86.5% accuracy; 15.9%
are assigned to manual review.

## Inputs and outputs

- **Input:** normalized complaint narrative text.
- **Output:** predicted product, routing confidence score, and review decision.
- **Target classes:** checking or savings account, credit card, credit reporting,
  debt collection, and mortgage.

Tokens not observed during training are ignored. No state, issue label, consumer
attribute, or protected characteristic is used as a model feature.

## Known limitations

- Results come from synthetic narratives and do not establish real-world
  accuracy.
- Naive Bayes scores are not guaranteed to be calibrated probabilities.
- Product definitions and language can change, lowering both accuracy and
  automation coverage.
- Short, multilingual, ambiguous, or copied narratives may require human
  judgment.
- Accuracy above the threshold does not measure the operational cost of routing
  a case to the wrong queue.

## Monitoring before any real use

Track accuracy and macro-F1 by product, threshold accuracy, review rate,
vocabulary drift, class mix, and re-routing frequency. Recalibrate the threshold
on a new labeled window when performance or coverage moves outside agreed
limits. Keep a human override and preserve an audit record of model suggestion,
confidence, final queue, and reviewer action.
