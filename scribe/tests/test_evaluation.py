from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.evaluation import (
    extract_numbers_and_units,
    number_unit_preservation,
    overcorrection_rate,
    score_correction,
    score_pair,
    split_terms,
    term_precision_recall_f1,
    term_recall,
    word_error_rate,
)


class EvaluationTests(unittest.TestCase):
    def test_word_error_rate_counts_substitution(self) -> None:
        self.assertAlmostEqual(word_error_rate("bệnh nhân đau ngực", "bệnh nhân đau bụng"), 0.25)

    def test_term_recall_uses_expected_terms_from_reference(self) -> None:
        self.assertEqual(term_recall("SpO2 98%", "spo2 98%", ["SpO2"]), 1.0)
        self.assertEqual(term_recall("SpO2 98%", "oxy 98%", ["SpO2"]), 0.0)

    def test_number_unit_preservation(self) -> None:
        self.assertIn("120mmhg", extract_numbers_and_units("120 mmHg"))
        self.assertEqual(number_unit_preservation("SpO2 98%", "SpO2 98%"), 1.0)

    def test_score_pair(self) -> None:
        metrics = score_pair("SpO2 98%", "SpO2 98%", ["SpO2"])
        self.assertEqual(metrics.wer, 0.0)
        self.assertEqual(metrics.term_recall, 1.0)
        self.assertEqual(metrics.term_precision, 1.0)
        self.assertEqual(metrics.term_f1, 1.0)

    def test_term_precision_recall_f1(self) -> None:
        metrics = term_precision_recall_f1("SpO2 98%", "SpO2 98% glucose", ["SpO2", "glucose"])
        self.assertEqual(metrics.true_positives, 1)
        self.assertEqual(metrics.false_positives, 1)
        self.assertEqual(metrics.false_negatives, 0)

    def test_score_correction_reports_overcorrection(self) -> None:
        metrics = score_correction(
            reference="bệnh nhân đau ngực",
            raw_hypothesis="bệnh nhân đau ngực",
            corrected_hypothesis="người bệnh đau ngực",
            terms=[],
        )
        self.assertGreater(metrics.overcorrection_rate, 0)

    def test_overcorrection_rate(self) -> None:
        self.assertEqual(
            overcorrection_rate("a b c", "a x c", "a y c"),
            0.0,
        )

    def test_split_terms(self) -> None:
        self.assertEqual(split_terms("testosterone; androgen"), ["testosterone", "androgen"])


if __name__ == "__main__":
    unittest.main()
