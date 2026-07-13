from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from types import SimpleNamespace

from carepath.services.asr import (
    GipformerASR,
    _merge_overlapping_text,
    _merge_text_windows,
    _plan_windows,
)


class _FakeStream:
    def __init__(self) -> None:
        self.result = SimpleNamespace(text="")
        self.payload: tuple[int, list] | None = None

    def accept_waveform(self, sample_rate, chunk) -> None:
        self.payload = (sample_rate, list(chunk))


class _FakeRecognizer:
    """Decodes a stream to 't<chunk_len>' so ordering is observable."""

    def __init__(self) -> None:
        self.decode_calls = 0

    def create_stream(self) -> _FakeStream:
        return _FakeStream()

    def decode_streams(self, streams) -> None:
        self.decode_calls += 1
        for stream in streams:
            stream.result.text = f"t{len(stream.payload[1])}"


class BatchedDecodeTests(unittest.TestCase):
    def test_decode_chunks_batches_once_and_keeps_positions(self) -> None:
        recognizer = _FakeRecognizer()
        chunks = [(16000, [0.1] * 3), (16000, []), (16000, [0.1] * 5)]
        texts = GipformerASR._decode_chunks(recognizer, chunks)
        # Empty chunk stays "" in place; one decode_streams call for the batch.
        self.assertEqual(texts, ["t3", "", "t5"])
        self.assertEqual(recognizer.decode_calls, 1)

    def test_combine_groups_merge_dedups_seam_and_join_spaces(self) -> None:
        groups = [([None, None], "merge"), ([None], "join"), ([None], "join")]
        text = GipformerASR._combine_groups(groups, ["a b c", "b c d", "e f", ""])
        self.assertEqual(text, "a b c d e f")


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
