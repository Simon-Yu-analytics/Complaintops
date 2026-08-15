from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sample" / "complaints.csv"
RNG = random.Random(20260815)

TEMPLATES = {
    "Credit reporting": {
        "Incorrect information on your report": [
            "My credit report lists an account that does not belong to me and the bureau has not corrected it",
            "I disputed an incorrect late payment but the information remains on my credit file",
            "The balance shown by the credit bureau is wrong and is hurting my score",
        ],
        "Improper use of your report": [
            "A company accessed my credit report without authorization and I need the inquiry removed",
            "I found a hard inquiry from a lender I never contacted",
        ],
    },
    "Credit card": {
        "Problem with a purchase": [
            "I was charged twice for the same card purchase and the duplicate charge was not reversed",
            "The merchant refund has not appeared on my credit card statement after several weeks",
        ],
        "Fees or interest": [
            "The card issuer charged an unexpected annual fee and would not explain the amount",
            "Interest was assessed even though I paid the statement balance by the due date",
        ],
    },
    "Checking or savings account": {
        "Managing an account": [
            "My checking account was frozen without notice and I cannot access my direct deposit",
            "The bank closed my savings account and has not returned the remaining balance",
        ],
        "Deposits and withdrawals": [
            "A cash deposit is missing from my account and the branch cannot locate it",
            "An unauthorized withdrawal appeared in my checking account",
        ],
    },
    "Debt collection": {
        "Attempts to collect debt not owed": [
            "A collector keeps calling about a debt that belongs to another person",
            "I paid this account years ago but a collection agency is demanding payment again",
        ],
        "Communication tactics": [
            "The debt collector calls repeatedly before work hours after I asked them to stop",
            "A collection company contacted my family members about my alleged debt",
        ],
    },
    "Mortgage": {
        "Trouble during payment process": [
            "My mortgage payment was applied to the wrong month and the servicer added a late fee",
            "The servicer changed my escrow payment without a clear calculation",
        ],
        "Applying for a mortgage": [
            "The lender delayed my mortgage application and repeatedly requested the same documents",
            "I was given a different interest rate at closing than the rate shown in my estimate",
        ],
    },
}

states = ["CA", "TX", "FL", "NY", "WA", "IL", "GA", "NC"]
channels = ["Web", "Phone", "Referral"]
start = date(2025, 1, 6)
rows = []
products = list(TEMPLATES)
for index in range(640):
    trend_weight = 0.20 + (index / 640) * 0.14
    weights = [trend_weight, 0.21, 0.20, 0.20, 0.19 - (index / 640) * 0.14]
    product = RNG.choices(products, weights=weights, k=1)[0]
    issue = RNG.choice(list(TEMPLATES[product]))
    narrative = RNG.choice(TEMPLATES[product][issue])
    narrative += RNG.choice([
        ". I contacted customer service but the issue is still unresolved.",
        ". I am requesting a written explanation and prompt correction.",
        ". This has created financial stress and needs urgent review.",
        ". The company has not provided a useful response.",
    ])
    received = start + timedelta(days=RNG.randrange(0, 245))
    rows.append(
        {
            "complaint_id": f"SYN-{index + 1:05d}",
            "date_received": received.isoformat(),
            "product": product,
            "issue": issue,
            "narrative": narrative,
            "state": RNG.choice(states),
            "submitted_via": RNG.choices(channels, [0.83, 0.10, 0.07], k=1)[0],
            "timely_response": RNG.choices(["Yes", "No"], [0.985, 0.015], k=1)[0],
        }
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: (row["date_received"], row["complaint_id"])))
print(f"Wrote {len(rows)} synthetic records to {OUTPUT}")

