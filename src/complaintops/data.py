from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "complaint_id",
    "date_received",
    "product",
    "issue",
    "narrative",
    "state",
    "submitted_via",
}


def load_complaints(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Complaint data is empty")
    missing = REQUIRED_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    for row in rows:
        datetime.strptime(row["date_received"], "%Y-%m-%d")
    return rows


def download_cfpb_sample(
    destination: str | Path,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    size: int = 5_000,
) -> Path:
    """Download a bounded public CFPB extract and map it to the local schema."""
    params = urllib.parse.urlencode(
        {
            "date_received_min": start_date,
            "date_received_max": end_date,
            "field": "all",
            "format": "json",
            "no_aggs": "true",
            "size": min(size, 10_000),
            "sort": "created_date_desc",
        }
    )
    url = (
        "https://www.consumerfinance.gov/data-research/consumer-complaints/"
        f"search/api/v1/?{params}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "ComplaintOps/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    hits = payload.get("hits", {}).get("hits", [])
    rows = []
    for hit in hits:
        source = hit.get("_source", hit)
        narrative = source.get("complaint_what_happened", "") or ""
        if not narrative.strip():
            continue
        rows.append(
            {
                "complaint_id": str(source.get("complaint_id", "")),
                "date_received": str(source.get("date_received", ""))[:10],
                "product": source.get("product", "Unknown"),
                "issue": source.get("issue", "Unknown"),
                "narrative": " ".join(narrative.split()),
                "state": source.get("state", "NA") or "NA",
                "submitted_via": source.get("submitted_via", "Unknown"),
                "timely_response": source.get("timely", "Unknown"),
            }
        )
    return write_rows(destination, rows)


def write_rows(path: str | Path, rows: Iterable[dict[str, str]]) -> Path:
    materialized = list(rows)
    if not materialized:
        raise ValueError("No rows to write")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)
    return destination

