from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from carepath.services.asr import (
    _merge_overlapping_text,
    _merge_text_windows,
    _plan_windows,
)


class PlanWindowsTests(unittest.TestCase):
    def test_fixed_windows_are_disjoint_and_cover_all_samples(self) -> None:
        windows = _plan_windows(25, window_samples=10, overlap_samples=0)
        self.assertEqual(windows, [(0, 10), (10, 20), (20, 25)])

    def test_overlap_windows_share_audio_at_the_seam(self) -> None:
        windows = _plan_windows(25, window_samples=10, overlap_samples=2)
        # step = 8; each window overlaps the previous by 2 samples.
        self.assertEqual(windows, [(0, 10), (8, 18), (16, 25)])

    def test_single_window_when_audio_shorter_than_window(self) -> None:
        self.assertEqual(_plan_windows(6, window_samples=10, overlap_samples=2), [(0, 6)])

    def test_empty_audio_yields_no_windows(self) -> None:
        self.assertEqual(_plan_windows(0, window_samples=10, overlap_samples=2), [])

    def test_overlap_capped_below_window_so_step_is_positive(self) -> None:
        # overlap >= window would stall; it is clamped to window-1 (step == 1).
        windows = _plan_windows(5, window_samples=3, overlap_samples=99)
        self.assertEqual(windows, [(0, 3), (1, 4), (2, 5)])


class MergeOverlappingTextTests(unittest.TestCase):
    def test_partial_seam_is_deduplicated(self) -> None:
        merged = _merge_overlapping_text(
            "bệnh nhân đau ngực nhiều", "đau ngực nhiều SpO2 98"
        )
        self.assertEqual(merged, "bệnh nhân đau ngực nhiều SpO2 98")

    def test_seam_match_is_case_insensitive_but_keeps_first_casing(self) -> None:
        merged = _merge_overlapping_text("đo SpO2", "spo2 chín mươi tám")
        self.assertEqual(merged, "đo SpO2 chín mươi tám")

    def test_no_shared_run_plain_joins_without_losing_words(self) -> None:
        merged = _merge_overlapping_text("huyết áp", "mạch nhanh")
        self.assertEqual(merged, "huyết áp mạch nhanh")

    def test_empty_sides(self) -> None:
        self.assertEqual(_merge_overlapping_text("", "xin chào"), "xin chào")
        self.assertEqual(_merge_overlapping_text("xin chào", ""), "xin chào")

    def test_merge_text_windows_folds_in_order(self) -> None:
        merged = _merge_text_windows(
            ["a b c", "b c d e", "d e f"]
        )
        self.assertEqual(merged, "a b c d e f")


if __name__ == "__main__":
    unittest.main()
