from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec import config
from gec.asr_lora import near_miss_status, validate_asr_runtime
from gec.candidates import (
    asr_benchmark,
    direct_asr_safety_report,
    duration_report,
    phonetic_candidate_gate,
    plain_asr_lora_gate,
    select_transcript_candidate,
)
from gec.data import (
    augment_training_pairs,
    select_variant_rows,
    validate_gec_pair,
    validate_synthetic_transcript,
)
from gec.datastore import build_datastore, extract_code_switch_terms, has_vietnamese_diacritics
from gec.evaluate import (
    aggregate_reports,
    mean_report,
    ne_f1_table,
    stratified_report,
    train_error_signal,
    wer_report,
)
from gec.gate import run_gate
from gec.leakage import duplicate_rejection_reason, ngram_overlap
from gec.metrics import score_pair, term_confusion, word_error_rate
from gec.nbest import dedupe_keep_order, diverse_hypotheses, other_hypotheses
from gec.phonetic import add_phonetic_corruption, corrupt_text
from gec.prompts import (
    build_synthetic_generation_messages,
    format_inference_prompt,
    format_training_prompt,
    parse_synthetic_transcripts,
)
from gec.synthetic import generate_synthetic_transcripts
from gec.train import (
    TrainArgs,
    _clear_attempt_locks,
    _package_versions,
    _qlora_backend,
    _resume_checkpoint,
    _unsloth_fast_language_model,
    train,
)


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


class QLoRABackendTests(unittest.TestCase):
    def test_backend_defaults_to_unsloth_and_accepts_only_explicit_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_qlora_backend(), "unsloth")
        for backend in ("unsloth", "hf"):
            with self.subTest(backend=backend), patch.dict(
                os.environ, {"CAREPATH_QLORA_BACKEND": backend}, clear=True
            ):
                self.assertEqual(_qlora_backend(), backend)
        for invalid in ("", "HF", "auto"):
            with self.subTest(invalid=invalid), patch.dict(
                os.environ, {"CAREPATH_QLORA_BACKEND": invalid}, clear=True
            ), self.assertRaisesRegex(ValueError, "unsloth.*hf"):
                _qlora_backend()

    def test_missing_unsloth_fails_with_explicit_hf_escape_hatch(self) -> None:
        with patch.dict(sys.modules, {"unsloth": None}), self.assertRaisesRegex(
            RuntimeError, "CAREPATH_QLORA_BACKEND=hf"
        ):
            _unsloth_fast_language_model()

    def test_run_versions_include_both_unsloth_packages(self) -> None:
        versions = _package_versions()
        self.assertIn("unsloth", versions)
        self.assertIn("unsloth-zoo", versions)

    def test_legacy_checkpoint_is_hf_and_cross_backend_resume_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "checkpoint-7").mkdir()
            self.assertTrue(_resume_checkpoint(output, "hf", resume=True).endswith("checkpoint-7"))
            with self.assertRaisesRegex(RuntimeError, "hf.*unsloth"):
                _resume_checkpoint(output, "unsloth", resume=True)

            (output / "training_run.json").write_text(
                json.dumps({"backend": "unsloth"}), encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "unsloth.*hf"):
                _resume_checkpoint(output, "hf", resume=True)

    def test_existing_checkpoint_metadata_must_name_a_valid_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "checkpoint-8").mkdir()
            run_file = output / "training_run.json"
            for metadata in ("{}", '{"backend": ""}', "not-json"):
                with self.subTest(metadata=metadata):
                    run_file.write_text(metadata, encoding="utf-8")
                    with self.assertRaisesRegex(RuntimeError, "refuse resume"):
                        _resume_checkpoint(output, "hf", resume=True)

    def test_same_backend_checkpoint_resumes_and_oom_locks_can_be_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "checkpoint-9").mkdir()
            run_file = output / "training_run.json"
            lock_file = output / "base_revision.json"
            for backend in ("unsloth", "hf"):
                run_file.write_text(json.dumps({"backend": backend}), encoding="utf-8")
                checkpoint = _resume_checkpoint(output, backend, resume=True)
                self.assertEqual(Path(checkpoint).name, "checkpoint-9")

            lock_file.write_text("{}", encoding="utf-8")
            _clear_attempt_locks(output)
            self.assertFalse(run_file.exists())
            self.assertFalse(lock_file.exists())

    def test_oom_model_fallback_clears_first_attempt_locks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            calls: list[str] = []

            def fake_train(_args, model_name):
                calls.append(model_name)
                if len(calls) == 1:
                    output.mkdir(exist_ok=True)
                    (output / "base_revision.json").write_text("{}", encoding="utf-8")
                    (output / "training_run.json").write_text("{}", encoding="utf-8")
                    raise RuntimeError("CUDA out of memory")

            with patch("gec.train._train", side_effect=fake_train):
                train(
                    TrainArgs(
                        pairs=output / "unused.jsonl",
                        output_dir=output,
                        base_model="primary",
                        fallback_model="fallback",
                    )
                )
            self.assertEqual(calls, ["primary", "fallback"])
            self.assertFalse((output / "base_revision.json").exists())
            self.assertFalse((output / "training_run.json").exists())


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
    def test_governed_datastore_default_never_reads_held_out_splits(self) -> None:
        class FakeDataset:
            column_names = ["cs_terms_list", "segment_text"]

            def select_columns(self, _columns):
                return self

            def __iter__(self):
                yield {"cs_terms_list": "train-term", "segment_text": "train-term"}

        from types import SimpleNamespace
        from unittest.mock import Mock, patch

        loader = Mock(return_value=FakeDataset())
        with patch.dict(sys.modules, {"datasets": SimpleNamespace(load_dataset=loader)}):
            payload = build_datastore(Path("missing-lexicon.json"), dataset="fake/dataset")
        self.assertEqual([call.kwargs["split"] for call in loader.call_args_list], ["train"])
        self.assertNotIn("hard-only-term", {item["term"] for item in payload["terms"]})

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

    def test_phonetic_mix_is_balanced_train_only_and_isolated(self) -> None:
        rows = [
            _pair(
                "train",
                "vimedcss_real",
                audio_id="r1",
                gold_text="bệnh nhân uống metformin 500 mg sáng nay",
                gold_terms=["metformin"],
            ),
            _pair("validation", "vimedcss_real", audio_id="v1"),
            _pair("hard", "vimedcss_real", audio_id="h1"),
        ]
        mixed = add_phonetic_corruption(rows, seed=13)
        train_sources = [row["source_kind"] for row in mixed if row["split"] == "train"]
        self.assertEqual(train_sources.count("pida_clean_text"), 1)
        self.assertEqual(train_sources.count("pida_phonetic_text"), 1)
        self.assertEqual(sum(row["split"] == "validation" for row in mixed), 1)
        self.assertEqual(sum(row["split"] == "hard" for row in mixed), 1)
        full, _ = select_variant_rows(mixed, "full")
        phonetic, _ = select_variant_rows(mixed, "phonetic")
        self.assertEqual({row["source_kind"] for row in full}, {"vimedcss_real"})
        self.assertEqual(
            {row["source_kind"] for row in phonetic},
            {"vimedcss_real", "pida_clean_text", "pida_phonetic_text"},
        )
        for row in mixed:
            if row["source_kind"].startswith("pida_"):
                self.assertIn("500", row["raw_asr"])
                self.assertIn("mg", row["raw_asr"])

    def test_each_phonetic_operation_is_deterministic(self) -> None:
        samples = {
            "tone": "bệnh nhân đau ngực",
            "vowel": "y tá chăm sóc",
            "consonant": "trẻ sốt cao",
            "code_switch_boundary": "bệnh nhân uống metformin hôm nay",
        }
        for operation, text in samples.items():
            terms = ["metformin"] if operation == "code_switch_boundary" else []
            first = corrupt_text(
                text, terms, seed=13, row_id=operation, preferred_operation=operation
            )
            second = corrupt_text(
                text, terms, seed=13, row_id=operation, preferred_operation=operation
            )
            self.assertEqual(first, second)
            self.assertNotEqual(first[0], text)

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

    def test_plain_asr_gate_and_explicit_proxy_labels(self) -> None:
        rows = self._rows()
        for row in rows:
            row["phowhisper_base"] = row["raw_asr"]
            row["phowhisper_pred"] = row["gold_text"]
        benchmark = asr_benchmark(
            rows, ("phowhisper_base", "phowhisper_pred")
        )
        gate = plain_asr_lora_gate(
            benchmark["metrics"], baseline="phowhisper_base"
        )
        self.assertTrue(gate["accepted"])
        clinical = benchmark["clinical_slices"]["phowhisper_pred"]["hard"]
        self.assertFalse(clinical["code_switch_term_error_proxy"]["is_pier"])
        self.assertEqual(clinical["pier"]["status"], "unavailable")

    def test_phonetic_gate_requires_full_baseline_and_safety(self) -> None:
        rows = self._rows()
        for row in rows:
            row["gec_full_pred"] = row["raw_asr"]
        report = wer_report(rows, ["gec_full_pred", "gec_pred"])
        frozen_rows = []
        for category in ("drug_name", "dosage", "numbers"):
            frozen_rows.append(
                {
                    "split": "frozen",
                    "category": category,
                    "gold_text": "uống metformin 500 mg",
                    "gold_terms": ["metformin"],
                    "gec_full_pred": "uong met pho min",
                    "gec_pred": "uống metformin 500 mg",
                }
            )
        decision = phonetic_candidate_gate(
            report,
            stratified_report(frozen_rows, ["gec_full_pred", "gec_pred"]),
        )
        self.assertTrue(decision["accepted"], decision["failures"])


class DirectAsrRuntimeTests(unittest.TestCase):
    def _rows(self) -> list[dict]:
        return EvalGateTests()._rows()

    def test_direct_asr_is_never_cpu_smoke(self) -> None:
        with self.assertRaisesRegex(ValueError, "Colab-only"):
            validate_asr_runtime(
                confirm_paid=True,
                cache_dir=Path("/content/cache"),
                in_colab=False,
                cuda_available=True,
            )
        with self.assertRaisesRegex(ValueError, "CUDA"):
            validate_asr_runtime(
                confirm_paid=True,
                cache_dir=Path("/content/cache"),
                in_colab=True,
                cuda_available=False,
            )

    def test_near_miss_reproduction_is_explicitly_fail_closed(self) -> None:
        blocked = near_miss_status(requested=True, plain_gate_accepted=False)
        self.assertEqual(blocked["status"], "blocked_plain_lora_gate")
        missing = near_miss_status(requested=True, plain_gate_accepted=True)
        self.assertEqual(missing["status"], "not_implemented")
        self.assertTrue(missing["blocking"])
        self.assertFalse(missing["executed"])
        self.assertEqual(missing["contract"]["genuine_beam_n_best"], 10)
        self.assertEqual(
            missing["contract"]["objective"]["poi_weighted_cross_entropy_alpha"],
            2.0,
        )

    def test_direct_asr_rejects_medication_regression_on_hard_evidence(self) -> None:
        rows = [
            {
                "split": "hard",
                "raw_asr": "metformin 500 mg",
                "phowhisper_pred": "met pho min 500 mg",
                "gold_text": "metformin 500 mg",
                "gold_terms": ["metformin"],
            },
            {
                "split": "hard",
                "raw_asr": "sp o hai 98 %",
                "phowhisper_pred": "SpO2 98 %",
                "gold_text": "SpO2 98 %",
                "gold_terms": ["SpO2"],
            },
        ]
        metrics = wer_report(rows, ["raw_asr", "phowhisper_pred"])
        safety = direct_asr_safety_report(rows, ("raw_asr", "phowhisper_pred"))
        selection = select_transcript_candidate(
            metrics,
            {},
            candidates=("raw_asr", "phowhisper_pred"),
            latency_seconds={"phowhisper_pred": 0.5},
            direct_safety_report=safety,
        )
        decision = selection["decisions"]["phowhisper_pred"]
        self.assertFalse(decision["eligible"])
        self.assertTrue(any("medication" in reason for reason in decision["reasons"]))

    def test_gate_rejects_regression(self) -> None:
        rows = self._rows()
        for row in rows:  # trained output is worse than raw
            row["gec_pred"] = row["raw_asr"] + " noise word"
        report = wer_report(rows, ["raw_asr", "gec_pred"])
        accepted, _ = run_gate(report, baselines=("raw_asr",))
        self.assertFalse(accepted)

    def test_gate_rejects_drug_regression_even_when_main_scores_improve(self) -> None:
        report = wer_report(self._rows(), ["raw_asr", "corrected_text", "gec_pred"])
        frozen = [
            {
                "category": "drug_name",
                "split": "frozen",
                "raw_asr": "uống metformin",
                "gold_text": "uống metformin",
                "gold_terms": ["metformin"],
                "gec_pred": "uống met pho min",
            },
            {
                "category": "dosage",
                "split": "frozen",
                "raw_asr": "uống 500 mg paracetamol",
                "gold_text": "uống 500 mg paracetamol",
                "gold_terms": ["paracetamol"],
                "gec_pred": "uống 500 mg paracetamol",
            },
        ]
        accepted, lines = run_gate(
            report,
            safety_report=stratified_report(frozen, ["raw_asr", "gec_pred"]),
        )
        self.assertFalse(accepted)
        self.assertIn("safety drug_name", "\n".join(lines))


class _StubRetriever:
    def retrieve(self, text, limit=None):  # noqa: D401 - test stub
        return []


class NbestTests(unittest.TestCase):
    def test_dedupe_keep_order(self) -> None:
        # case/whitespace duplicates collapse; empties drop; first-seen order kept.
        self.assertEqual(dedupe_keep_order(["A b", "a  b", "", "c"]), ["A b", "c"])

    def test_other_hypotheses_single_best_is_empty(self) -> None:
        # n_best <= 1 keeps the cheap single-decode path (no asr/audio needed).
        self.assertEqual(other_hypotheses(None, "missing.wav", "best", 1), [])

    def test_diverse_hypotheses_n1_returns_best_only(self) -> None:
        self.assertEqual(diverse_hypotheses(None, "missing.wav", n=1, best_text="best"), ["best"])

    def test_diverse_hypotheses_perturbation_best_first_and_deterministic(self) -> None:
        try:
            import numpy as np  # type: ignore
            import soundfile as sf  # type: ignore
        except Exception:  # pragma: no cover - optional deps
            self.skipTest("numpy/soundfile not installed")
        import tempfile
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "clip.wav"
            sf.write(str(wav), (0.1 * np.sin(np.linspace(0, 50, 8000))).astype("float32"), 16000)

            def make_stub():
                state = {"n": 0}

                def transcribe(_path):
                    state["n"] += 1
                    return SimpleNamespace(text=f"hyp{state['n']}")

                return SimpleNamespace(transcribe=transcribe)

            hyps = diverse_hypotheses(make_stub(), wav, n=3, best_text="best", seed=7)
            self.assertEqual(hyps[0], "best")
            self.assertEqual(len(hyps), 3)
            self.assertEqual(hyps, diverse_hypotheses(make_stub(), wav, n=3, best_text="best", seed=7))

    def test_diverse_hypotheses_uses_transcribe_batch_in_one_call(self) -> None:
        try:
            import numpy as np  # type: ignore
            import soundfile as sf  # type: ignore
        except Exception:  # pragma: no cover - optional deps
            self.skipTest("numpy/soundfile not installed")
        import tempfile
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "clip.wav"
            sf.write(str(wav), (0.1 * np.sin(np.linspace(0, 50, 8000))).astype("float32"), 16000)

            calls: list[int] = []

            def transcribe_batch(paths):
                calls.append(len(paths))
                return [SimpleNamespace(text=f"hyp{i}") for i in range(len(paths))]

            stub = SimpleNamespace(transcribe=None, transcribe_batch=transcribe_batch)
            hyps = diverse_hypotheses(stub, wav, n=5, best_text="best", seed=7)
            self.assertEqual(calls, [5])  # all perturbations in one batched decode
            self.assertEqual(hyps[0], "best")
            self.assertEqual(len(hyps), 5)


class WordWerTests(unittest.TestCase):
    def test_segmented_wer_matches_for_ascii(self) -> None:
        # pyvi leaves ascii tokens alone (and falls back to split if absent).
        self.assertAlmostEqual(word_error_rate("a b c", "a b d", segment=True), 1 / 3)


class AggregateTests(unittest.TestCase):
    def test_aggregate_and_mean_report(self) -> None:
        r1 = {"gec_pred": {"validation": {"wer": 0.2, "term_f1": 0.8}}}
        r2 = {"gec_pred": {"validation": {"wer": 0.4, "term_f1": 0.6}}}
        agg = aggregate_reports([r1, r2])
        self.assertAlmostEqual(agg["gec_pred"]["validation"]["wer"]["mean"], 0.3)
        self.assertEqual(agg["gec_pred"]["validation"]["wer"]["n_seeds"], 2)
        self.assertAlmostEqual(mean_report([r1, r2])["gec_pred"]["validation"]["wer"], 0.3)


class ErrorSignalTests(unittest.TestCase):
    def test_thin_vs_rich_signal(self) -> None:
        thin = train_error_signal(
            [{"split": "train", "raw_asr": "bệnh nhân đo SpO2", "gold_text": "bệnh nhân đo SpO2"}]
        )
        self.assertTrue(thin["thin_signal"])
        rich = train_error_signal(
            [{"split": "train", "raw_asr": "benh nhan", "gold_text": "bệnh nhân đo SpO2 chín tám"}]
        )
        self.assertFalse(rich["thin_signal"])


class TranscriptCandidateTests(unittest.TestCase):
    def test_duration_is_computed_from_rows(self) -> None:
        report = duration_report([{"duration_seconds": 1_800}, {"duration_seconds": 900}, {}])
        self.assertEqual(report["hours"], 0.75)
        self.assertEqual(report["rows_missing_duration"], 1)

    def test_asr_benchmark_declares_single_best(self) -> None:
        rows = [
            {
                "split": "hard",
                "raw_asr": "met pho min",
                "gold_text": "metformin",
                "gold_terms": ["metformin"],
                "duration_seconds": 2,
            }
        ]
        report = asr_benchmark(rows)
        self.assertEqual(report["hypothesis_source"], "single_best")
        self.assertEqual(report["duration"]["source"], "pair_duration_seconds")

    def test_selection_uses_safety_gate_then_term_error(self) -> None:
        rows = [
            {
                "split": split,
                "raw_asr": "met pho min 50 mg",
                "gold_text": "metformin 500 mg",
                "gold_terms": ["metformin"],
                "gec_pred": "metformin 500 mg",
            }
            for split in ("validation", "hard")
        ]
        frozen = [
            {
                "category": category,
                "split": "frozen",
                "raw_asr": "met pho min 50 mg",
                "gold_text": "metformin 500 mg",
                "gold_terms": ["metformin"],
                "gec_pred": "metformin 500 mg",
            }
            for category in ("drug_name", "dosage")
        ]
        selected = select_transcript_candidate(
            wer_report(rows, ["raw_asr", "gec_pred"]),
            stratified_report(frozen, ["raw_asr", "gec_pred"]),
        )
        self.assertEqual(selected["selected"], "gec_pred")


if __name__ == "__main__":
    unittest.main()
