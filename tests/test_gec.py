from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from carepath.gec import config
from carepath.gec.data import (
    augment_training_pairs,
    select_variant_rows,
    validate_gec_pair,
    validate_synthetic_transcript,
)
from carepath.gec.datastore import extract_code_switch_terms, has_vietnamese_diacritics
from carepath.gec.evaluate import ne_f1_table, wer_report
from carepath.gec.gate import run_gate
from carepath.gec.leakage import duplicate_rejection_reason, ngram_overlap
from carepath.gec.metrics import TermConfusion, score_pair, term_confusion, word_error_rate
from carepath.gec.prompts import (
    build_synthetic_generation_messages,
    format_inference_prompt,
    format_training_prompt,
    parse_synthetic_transcripts,
)
from carepath.gec.synthetic import generate_synthetic_transcripts


def _pair(split: str, source: str, **over) -> dict:
    base = {
        "split": split,
        "source_kind": source,
        "audio_id": over.get("audio_id", f"{split}-{source}"),
        "raw_asr": "benh nhan do spo2",
        "gold_text": "bệnh nhân đo SpO2",
        "gold_terms": ["SpO2"],
        "retrieved_terms": ["SpO2"],
        "asr_model": "mock",
    }
    base.update(over)
    return base


class PromptTests(unittest.TestCase):
    def test_inference_prompt_stops_at_assistant_and_hides_gold(self) -> None:
        row = {"raw_asr": "spo2 chin muoi tam", "gold_text": "SpO2 chín mươi tám",
               "retrieved_terms": ["SpO2"]}
        inference = format_inference_prompt(row)
        self.assertTrue(inference.endswith("<|im_start|>assistant\n"))
        self.assertIn("SpO2", inference)
        self.assertNotIn(row["gold_text"], inference)
        training = format_training_prompt(row)
        self.assertTrue(training.startswith(inference))
        self.assertIn(row["gold_text"], training)

    def test_wo_rac_prompt_drops_named_entities(self) -> None:
        row = {"raw_asr": "x", "gold_text": "y", "retrieved_terms": ["SpO2"]}
        self.assertIn("Named entities", format_inference_prompt(row, use_retrieval=True))
        self.assertNotIn("Named entities", format_inference_prompt(row, use_retrieval=False))

    def test_synthetic_messages_and_parse(self) -> None:
        messages = build_synthetic_generation_messages(
            [{"segment_text": "bệnh nhân đo SpO2 98%", "cs_terms_list": "SpO2"}], count=2
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("exactly 2", messages[1]["content"])
        rows = parse_synthetic_transcripts(
            '{"transcripts":[{"clean_text":"bệnh nhân đau ngực SpO2 98%","intended_terms":["SpO2"]}]}'
        )
        self.assertEqual(rows[0]["intended_terms"], ["SpO2"])


class MetricTests(unittest.TestCase):
    def test_word_error_rate(self) -> None:
        self.assertAlmostEqual(word_error_rate("a b c", "a b d"), 1 / 3)
        self.assertEqual(word_error_rate("", ""), 0.0)

    def test_term_confusion_micro_f1(self) -> None:
        # term present in gold + hypothesis -> TP; missing in hypothesis -> FN.
        tp = term_confusion("uống metformin", "uống metformin", ["metformin"])
        self.assertEqual((tp.true_positives, tp.false_negatives), (1, 0))
        fn = term_confusion("uống metformin", "uong met pho min", ["metformin"])
        self.assertEqual((fn.true_positives, fn.false_negatives), (0, 1))
        combined = tp + fn
        self.assertAlmostEqual(combined.recall, 0.5)

    def test_score_pair_number_unit_preservation(self) -> None:
        metrics = score_pair("spo2 98 %", "spo2 90 %", ["spo2"])
        self.assertLess(metrics.number_unit_preservation, 1.0)


class DatastoreTests(unittest.TestCase):
    def test_diacritic_detection(self) -> None:
        self.assertTrue(has_vietnamese_diacritics("bệnh"))
        self.assertFalse(has_vietnamese_diacritics("metformin"))

    def test_extract_code_switch_terms(self) -> None:
        terms = extract_code_switch_terms("bệnh nhân đo SpO2 và HbA1c rồi uống metformin")
        self.assertIn("SpO2", terms)
        self.assertIn("HbA1c", terms)
        self.assertIn("metformin", terms)
        # Vietnamese (diacritic) words must not be mined as NEs.
        self.assertNotIn("bệnh", terms)


class DataAndVariantTests(unittest.TestCase):
    def test_validate_gec_pair(self) -> None:
        self.assertTrue(validate_gec_pair(_pair("train", "vimedcss_real")).ok)
        bad = _pair("train", "random_typos")
        self.assertFalse(validate_gec_pair(bad).ok)

    def test_validate_synthetic_transcript(self) -> None:
        ok = validate_synthetic_transcript({
            "source_kind": "darag_synthetic_clean",
            "synthetic_id": "s1",
            "clean_text": "bệnh nhân đau ngực SpO2 chín mươi tám phần trăm",
            "topic": "tim mạch",
            "seed_example_ids": ["a"],
            "model": "Qwen/Qwen3-4B-Instruct-2507",
        })
        self.assertTrue(ok.ok)

    def test_augment_only_touches_train(self) -> None:
        real = [
            _pair("train", "vimedcss_real", audio_id="r1"),
            _pair("validation", "vimedcss_real", audio_id="v1"),
            _pair("hard", "vimedcss_real", audio_id="h1"),
        ]
        synth = [_pair("train", "darag_synthetic_tts", audio_id="s1")]
        merged = augment_training_pairs(real, synth, nsyn_factor=1.0)
        splits = sorted(r["split"] for r in merged)
        self.assertEqual(splits, ["hard", "train", "train", "validation"])
        self.assertTrue(any(r["source_kind"] == "darag_synthetic_tts" for r in merged))

    def test_select_variant_rows(self) -> None:
        pairs = [
            _pair("train", "vimedcss_real", audio_id="r1"),
            _pair("train", "darag_synthetic_tts", audio_id="s1"),
            _pair("validation", "vimedcss_real", audio_id="v1"),
        ]
        full, use = select_variant_rows(pairs, "full")
        self.assertEqual(len(full), 2)
        self.assertTrue(use)
        wo_rac, use = select_variant_rows(pairs, "wo_rac")
        self.assertEqual(len(wo_rac), 2)
        self.assertFalse(use)  # NEs stripped from the prompt
        wo_aug, _ = select_variant_rows(pairs, "wo_aug")
        self.assertTrue(all(r["source_kind"] == "vimedcss_real" for r in wo_aug))
        only_synth, _ = select_variant_rows(pairs, "only_synth")
        self.assertTrue(all(r["source_kind"] == "darag_synthetic_tts" for r in only_synth))

    def test_variant_uses_retrieval(self) -> None:
        self.assertFalse(config.variant_uses_retrieval("wo_rac"))
        self.assertTrue(config.variant_uses_retrieval("full"))
        with self.assertRaises(ValueError):
            config.variant_uses_retrieval("nope")


class LeakageTests(unittest.TestCase):
    def test_ngram_overlap_and_rejection(self) -> None:
        self.assertGreater(ngram_overlap("a b c d", "a b c d"), 0.9)
        reason = duplicate_rejection_reason("a b c d e", ["a b c d e"])
        self.assertIsNotNone(reason)
        self.assertIsNone(duplicate_rejection_reason("totally different words here", ["a b c d e"]))


class SyntheticLoopTests(unittest.TestCase):
    def test_generate_with_stub_generator_dedupes(self) -> None:
        examples = [{"segment_text": "bệnh nhân đo SpO2 chín tám phần trăm", "cs_terms_list": "SpO2"}]
        calls = {"n": 0}

        def fake_generate(_messages):
            calls["n"] += 1
            # First batch returns a fresh transcript; later batches repeat it (rejected).
            text = "đo huyết áp và nhịp tim mỗi sáng" if calls["n"] == 1 else "bệnh nhân đo SpO2 chín tám phần trăm"
            return '{"transcripts":[{"clean_text":"%s","intended_terms":[]}]}' % text

        rows = generate_synthetic_transcripts(
            examples=examples, count=1, generate_fn=fake_generate, batch_size=1, max_iterations=5
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["clean_text"], "đo huyết áp và nhịp tim mỗi sáng")


class EvalGateTests(unittest.TestCase):
    def _rows(self) -> list[dict]:
        return [
            {"split": "validation", "raw_asr": "uong met pho min", "gold_text": "uống metformin",
             "gold_terms": ["metformin"], "corrected_text": "uong met pho min",
             "gec_pred": "uống metformin"},
            {"split": "hard", "raw_asr": "chi so hba", "gold_text": "chỉ số HbA1c",
             "gold_terms": ["HbA1c"], "corrected_text": "chi so hba", "gec_pred": "chỉ số HbA1c"},
        ]

    def test_ne_f1_table_methods_and_groups(self) -> None:
        table = ne_f1_table(self._rows())
        self.assertEqual(table["Baseline"]["ID"]["f1_micro"], 0.0)
        self.assertEqual(table["+DARAG"]["ID"]["f1_micro"], 1.0)
        self.assertEqual(table["+DARAG"]["OOD"]["f1_micro"], 1.0)
        self.assertNotIn("+DARAG w/ ID NE", table)  # column absent -> skipped

    def test_gate_accepts_winning_candidate(self) -> None:
        report = wer_report(self._rows(), ["raw_asr", "corrected_text", "gec_pred"])
        accepted, lines = run_gate(report)
        self.assertTrue(accepted, msg="\n".join(lines))

    def test_gate_rejects_regression(self) -> None:
        rows = self._rows()
        for row in rows:  # trained output is worse than raw
            row["gec_pred"] = row["raw_asr"] + " noise word"
        report = wer_report(rows, ["raw_asr", "gec_pred"])
        accepted, _ = run_gate(report, baselines=("raw_asr",))
        self.assertFalse(accepted)


if __name__ == "__main__":
    unittest.main()
