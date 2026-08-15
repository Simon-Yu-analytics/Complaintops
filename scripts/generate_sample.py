"""Generate a deterministic, privacy-safe complaint operations dataset."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sample" / "complaints.csv"
RNG = random.Random(20260815)
START = date(2025, 1, 6)

TEMPLATES = {
    "Credit reporting": {
        "Incorrect information on your report": [
            "an account I do not recognize remains on my credit file",
            "an incorrect late payment is still shown after my dispute",
            "the balance reported by the credit bureau is inaccurate",
            "identity-theft information was reinserted after being removed",
        ],
        "Improper use of your report": [
            "a hard inquiry appeared from a lender I never contacted",
            "my credit file was accessed without a permissible purpose",
            "a screening company shared my report without authorization",
        ],
    },
    "Credit card": {
        "Problem with a purchase": [
            "the same card purchase was charged twice",
            "a merchant refund never appeared on my card statement",
            "a card transaction I did not authorize was approved",
            "the issuer rejected my chargeback without reviewing the receipt",
        ],
        "Fees or interest": [
            "the issuer added an annual fee that was not disclosed",
            "interest was assessed after I paid the statement balance",
            "a promotional rate ended earlier than the offer stated",
        ],
    },
    "Checking or savings account": {
        "Managing an account": [
            "my checking account was frozen without advance notice",
            "the bank closed my savings account and retained the balance",
            "online access was disabled after I verified my identity",
            "the account was placed under review with no completion date",
        ],
        "Deposits and withdrawals": [
            "a cash deposit is missing from my account",
            "an unauthorized withdrawal appeared in checking",
            "a mobile check deposit was reversed without explanation",
        ],
    },
    "Debt collection": {
        "Attempts to collect debt not owed": [
            "a collector is pursuing a balance that belongs to someone else",
            "a paid account was sent to collections again",
            "the agency cannot validate the amount it says I owe",
            "the debt is beyond the applicable reporting period",
        ],
        "Communication tactics": [
            "the collector calls repeatedly before permitted hours",
            "the agency contacted relatives about the alleged debt",
            "calls continued after my written request to stop",
        ],
    },
    "Mortgage": {
        "Trouble during payment process": [
            "my mortgage payment was applied to the wrong month",
            "the servicer changed the escrow amount without a calculation",
            "a completed payment was returned and then marked late",
            "the payoff balance includes charges I cannot reconcile",
        ],
        "Applying for a mortgage": [
            "the lender repeatedly requested documents already provided",
            "the closing rate differed from the loan estimate",
            "the application remained pending after the promised decision date",
        ],
    },
}

VOLUME = {
    "Credit reporting": (30, 0.24, 3.6, 0.0),
    "Credit card": (23, 0.04, 3.2, 2.0),
    "Checking or savings account": (19, 0.06, 2.7, 4.0),
    "Debt collection": (20, 0.08, 2.4, 1.0),
    "Mortgage": (17, -0.07, 2.0, 3.0),
}

LEADS = [
    "I am filing this complaint because",
    "After reviewing my records, I found that",
    "I need help resolving a situation where",
    "The company has not corrected a problem in which",
    "My records show that",
]
CONTEXT = [
    "Customer service transferred me twice without resolving it",
    "I supplied supporting documents through the online portal",
    "The first written response did not address the evidence",
    "This is affecting my ability to manage upcoming payments",
    "I called and also sent a secure message to the company",
    "The issue has continued despite a prior case being marked closed",
]
REQUESTS = [
    "I am requesting a written explanation and correction",
    "Please investigate the records and provide a clear resolution date",
    "I want the company to review the evidence and correct the account",
    "I need an itemized response that explains the decision",
]
STATES = ["CA", "TX", "FL", "NY", "WA", "IL", "GA", "NC"]
CHANNELS = ["Web", "Phone", "Referral"]


def weekly_volume(product: str, week: int) -> int:
    base, trend, amplitude, phase = VOLUME[product]
    seasonal = amplitude * math.sin(2 * math.pi * (week + phase) / 13)
    shock = 0
    if product == "Credit card" and week in {46, 47, 48}:
        shock = 6
    if product == "Credit reporting" and week in {20, 21}:
        shock = 5
    return max(6, round(base + trend * week + seasonal + shock + RNG.gauss(0, 1.7)))


def phrase_for(product: str) -> tuple[str, str]:
    issue = RNG.choice(list(TEMPLATES[product]))
    return issue, RNG.choice(TEMPLATES[product][issue])


def narrative_for(product: str, week: int) -> tuple[str, str]:
    issue, primary = phrase_for(product)
    clauses = [f"{RNG.choice(LEADS)} {primary}.", f"{RNG.choice(CONTEXT)}."]
    # Real intake can mention several products. Overlapping stories keep the
    # synthetic benchmark from making routing look unrealistically perfect.
    if RNG.random() < 0.22:
        other = RNG.choice([name for name in TEMPLATES if name != product])
        _, overlapping = phrase_for(other)
        clauses.append(f"The same interaction also mentioned that {overlapping}.")
    if RNG.random() < 0.09:
        other = RNG.choice([name for name in TEMPLATES if name != product])
        _, ambiguous = phrase_for(other)
        clauses[0] = f"{RNG.choice(LEADS)} {ambiguous}."
    clauses.append(f"I have been trying to resolve this for {RNG.randint(7, 90)} days.")
    clauses.append(f"{RNG.choice(REQUESTS)}.")
    if week >= 39 and RNG.random() < 0.35:
        clauses.append("The latest response was an automated message with no case owner.")
    return issue, " ".join(clauses)


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_narratives: set[str] = set()
    complaint_number = 1
    for week in range(52):
        for product in TEMPLATES:
            for _ in range(weekly_volume(product, week)):
                issue, narrative = narrative_for(product, week)
                if narrative in seen_narratives:
                    narrative += (
                        f" My follow-up reference is SYN-{complaint_number:05d}."
                    )
                seen_narratives.add(narrative)
                received = START + timedelta(days=week * 7 + RNG.randrange(0, 7))
                rows.append(
                    {
                        "complaint_id": f"SYN-{complaint_number:05d}",
                        "date_received": received.isoformat(),
                        "product": product,
                        "issue": issue,
                        "narrative": narrative,
                        "state": RNG.choice(STATES),
                        "submitted_via": RNG.choices(CHANNELS, [0.83, 0.10, 0.07], k=1)[0],
                        "timely_response": RNG.choices(["Yes", "No"], [0.985, 0.015], k=1)[0],
                    }
                )
                complaint_number += 1
    return sorted(rows, key=lambda row: (str(row["date_received"]), str(row["complaint_id"])))


def main() -> None:
    RNG.seed(20260815)
    rows = build_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic records to {OUTPUT}")


if __name__ == "__main__":
    main()
