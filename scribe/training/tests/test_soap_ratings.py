from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))

from scripts.validate_soap_ratings import summarize_ratings  # noqa: E402


def _row(note_id: str, **overrides: str) -> dict[str, str]:
    row = {
        "note_id": note_id,
        "clinician_id": "reviewer-a",
        "completeness": "4",
        "hallucination": "0",
        "terminology": "5",
        "reviewed_at": "2026-07-13T12:00:00+07:00",
        "status": "accepted",
    }
    row.update(overrides)
    return row


class SoapRatingsTests(unittest.TestCase):
    def test_summary_reports_unique_notes_without_a_readiness_gate(self) -> None:
        rows = [_row("note-1"), _row("note-1"), _row("note-2")]
        summary = summarize_ratings(rows)
        self.assertEqual(summary["rating_rows"], 3)
        self.assertEqual(summary["unique_notes"], 2)
        self.assertNotIn("ready_for_decision", summary)

    def test_summary_reports_serious_hallucinations(self) -> None:
        rows = [_row("note-1", hallucination="2", status="unsafe")]
        summary = summarize_ratings(rows)
        self.assertEqual(summary["serious_hallucinations"], 1)
        self.assertEqual(summary["unsafe_notes"], 1)

    def test_rejects_out_of_range_score(self) -> None:
        with self.assertRaisesRegex(ValueError, "hallucination"):
            summarize_ratings([_row("note-1", hallucination="4")])

    def test_rejects_invalid_review_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "reviewed_at"):
            summarize_ratings([_row("note-1", reviewed_at="today")])
