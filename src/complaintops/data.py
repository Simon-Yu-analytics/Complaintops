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
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("Complaint data is empty")
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        empty = [column for column in REQUIRED_COLUMNS if not (row.get(column) or "").strip()]
        if empty:
            raise ValueError(f"Row {row_number} has empty required fields: {sorted(empty)}")
        complaint_id = row["complaint_id"].strip()
        if complaint_id in seen_ids:
            raise ValueError(f"Duplicate complaint_id at row {row_number}: {complaint_id}")
        seen_ids.add(complaint_id)
        try:
            datetime.strptime(row["date_received"], "%Y-%m-%d")
        except ValueError as error:
            raise ValueError(
                f"Invalid date_received at row {row_number}: {row['date_received']}"
            ) from error
    return rows


def download_cfpb_sample(
    destination: str | Path,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    size: int = 5_000,
) -> Path:
    """Download a bounded public CFPB extract and map it to the local schema."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    if size <= 0:
        raise ValueError("size must be positive")
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
    request = urllib.request.Request(url, headers={"User-Agent": "ComplaintOps/1.0"})
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
