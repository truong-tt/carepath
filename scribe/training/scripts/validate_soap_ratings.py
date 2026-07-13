"""Validate a de-identified clinician SOAP-rating export without reading note content."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = (
    "note_id",
    "clinician_id",
    "completeness",
    "hallucination",
    "terminology",
    "reviewed_at",
    "status",
)
SCORE_LIMITS = {"completeness": (1, 5), "hallucination": (0, 3), "terminology": (1, 5)}
STATUSES = {"accepted", "needs_correction", "unsafe"}


def summarize_ratings(rows: list[dict[str, str]], min_notes: int = 50) -> dict[str, object]:
    if not rows:
        raise ValueError("rating export has no rows")
    notes: set[str] = set()
    totals = {field: 0 for field in SCORE_LIMITS}
    unsafe = 0
    serious_hallucinations = 0
    for number, row in enumerate(rows, start=2):
        if set(row) != set(REQUIRED_COLUMNS):
            raise ValueError(f"row {number}: rating export columns do not match the approved schema")
        if any(not row[column].strip() for column in REQUIRED_COLUMNS):
            raise ValueError(f"row {number}: required rating value is empty")
        try:
            datetime.fromisoformat(row["reviewed_at"])
        except ValueError as exc:
            raise ValueError(f"row {number}: reviewed_at must be ISO 8601") from exc
        notes.add(row["note_id"].strip())
        for field, (low, high) in SCORE_LIMITS.items():
            try:
                value = int(row[field])
            except ValueError as exc:
                raise ValueError(f"row {number}: {field} must be an integer") from exc
            if not low <= value <= high:
                raise ValueError(f"row {number}: {field} must be between {low} and {high}")
            totals[field] += value
        if row["status"] not in STATUSES:
            raise ValueError(f"row {number}: status must be one of {sorted(STATUSES)}")
        unsafe += row["status"] == "unsafe"
        serious_hallucinations += int(row["hallucination"]) >= 2
    count = len(rows)
    return {
        "rating_rows": count,
        "unique_notes": len(notes),
        "mean_completeness": round(totals["completeness"] / count, 2),
        "mean_hallucination": round(totals["hallucination"] / count, 2),
        "mean_terminology": round(totals["terminology"] / count, 2),
        "serious_hallucinations": serious_hallucinations,
        "unsafe_notes": unsafe,
        "ready_for_decision": len(notes) >= min_notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--min-notes", type=int, default=50)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as stream:
        summary = summarize_ratings(list(csv.DictReader(stream)), args.min_notes)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
