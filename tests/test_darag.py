from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from hopegait.darag import (
    build_synthetic_generation_messages,
    duplicate_rejection_reason,
    format_darag_training_prompt,
    parse_synthetic_transcripts,
    validate_gec_pair,
    validate_synthetic_transcript,
)


class DaragTests(unittest.TestCase):
    def test_validate_gec_pair_accepts_real_pair_schema(self) -> None:
        row = {
            "split": "train",
            "source_kind": "vimedcss_real",
            "audio_id": "abc",
            "raw_asr": "benh nhan dau nguc spo2",
            "gold_text": "bệnh nhân đau ngực SpO2",
            "gold_terms": ["SpO2"],
            "retrieved_terms": ["SpO2"],
            "asr_model": "gipformer",
            "duration_seconds": 1.0,
        }
        self.assertTrue(validate_gec_pair(row).ok)

    def test_validate_gec_pair_rejects_random_typo_rows_without_source_label(self) -> None:
        row = {
            "split": "train",
            "source_kind": "random_typos",
            "audio_id": "abc",
            "raw_asr": "benh nhan",
            "gold_text": "bệnh nhân",
            "gold_terms": [],
            "retrieved_terms": [],
            "asr_model": "manual",
            "duration_seconds": None,
        }
        self.assertFalse(validate_gec_pair(row).ok)

    def test_format_darag_training_prompt_includes_retrieved_terms(self) -> None:
        prompt = format_darag_training_prompt(
            {
                "raw_asr": "spo2 chin muoi tam",
                "gold_text": "SpO2 chín mươi tám",
                "retrieved_terms": ["SpO2"],
            }
        )
        self.assertIn("SpO2", prompt)
        self.assertIn("Raw ASR transcript", prompt)

    def test_parse_synthetic_transcripts_from_json_object(self) -> None:
        rows = parse_synthetic_transcripts(
            '{"transcripts":[{"clean_text":"bệnh nhân đau ngực SpO2 98%",'
            '"topic":"tim mạch","intended_terms":["SpO2"]}]}'
        )
        self.assertEqual(rows[0]["intended_terms"], ["SpO2"])

    def test_validate_synthetic_transcript(self) -> None:
        result = validate_synthetic_transcript(
            {
                "source_kind": "darag_synthetic_clean",
                "synthetic_id": "s1",
                "clean_text": "bệnh nhân đau ngực SpO2 chín mươi tám phần trăm",
                "topic": "tim mạch",
                "seed_example_ids": ["a"],
                "model": "Qwen/Qwen3-4B-Instruct-2507",
            }
        )
        self.assertTrue(result.ok)

    def test_duplicate_rejection_reason(self) -> None:
        reason = duplicate_rejection_reason(
            "bệnh nhân đau ngực SpO2 chín mươi tám phần trăm",
            ["bệnh nhân đau ngực SpO2 chín mươi tám phần trăm"],
        )
        self.assertIsNotNone(reason)

    def test_build_synthetic_generation_messages(self) -> None:
        messages = build_synthetic_generation_messages(
            [{"segment_text": "bệnh nhân đau ngực SpO2 98%", "cs_terms_list": "SpO2"}],
            count=2,
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("exactly 2", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
