from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))

from carepath.services.gec_local import LocalGecLLM  # noqa: E402
from carepath.services.llm import OfflineClinicalLLM  # noqa: E402
from carepath.services.retrieval import RetrievedTerm  # noqa: E402
from gec.baseline import build_baseline_report  # noqa: E402
from gec.evaluate import stratified_report  # noqa: E402
from gec.manifest import load_manifest, sha256_file  # noqa: E402
from gec.run_config import load_pipeline_config  # noqa: E402

FIXTURE = ROOT / "scribe" / "training" / "eval" / "fixtures" / "gec_eval_v1.jsonl"
FIXTURE_MANIFEST = ROOT / "scribe" / "training" / "eval" / "fixtures" / "gec_eval_v1.manifest.json"
BASELINE_CONFIG = ROOT / "scribe" / "training" / "configs" / "frozen-baseline-v1.json"
BASELINE_REPORT = ROOT / "scribe" / "training" / "reports" / "gec-frozen-baseline-v1.json"


class DatasetManifestTests(unittest.TestCase):
    def test_frozen_fixture_hash_matches_its_manifest(self) -> None:
        manifest = load_manifest(FIXTURE_MANIFEST)
        self.assertEqual(manifest["sha256"], sha256_file(FIXTURE))

    def test_training_requires_owner_approved_manifest(self) -> None:
        with self.assertRaisesRegex(ValueError, "owner-approved"):
            load_manifest(ROOT / "scribe" / "training" / "manifests" / "vimedcss-v1.json", require_approved=True)

    def test_pipeline_train_stops_before_any_model_step_without_approval(self) -> None:
        result = subprocess.run(
            [sys.executable, "scribe/training/scripts/run_pipeline.py", "--stage", "train"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("owner-approved consent", result.stderr)


class PipelineConfigTests(unittest.TestCase):
    def test_versioned_config_has_fixed_unique_seeds(self) -> None:
        config = load_pipeline_config(ROOT / "scribe" / "training" / "configs" / "full-v1.json")
        self.assertEqual(config.run_id, "carepath-gec-full-v1")
        self.assertEqual(config.profile.seeds, (13, 7, 42))

    def test_duplicate_seeds_are_rejected(self) -> None:
        payload = json.loads((ROOT / "scribe" / "training" / "configs" / "smoke-v1.json").read_text(encoding="utf-8"))
        payload["profile"]["seeds"] = [13, 13]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique fixed seeds"):
                load_pipeline_config(path)


class StratifiedEvaluationTests(unittest.TestCase):
    def test_frozen_fixture_reports_every_safety_category(self) -> None:
        rows = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines()]
        report = stratified_report(rows, ["raw_asr"])

        self.assertEqual(
            set(report), {"diacritics", "dosage", "drug_name", "laterality", "negation", "numbers"}
        )
        self.assertTrue(all(metrics["raw_asr"]["frozen"]["n"] == 2 for metrics in report.values()))


class BaselineAndExportTests(unittest.TestCase):
    def test_committed_baseline_matches_the_frozen_fixture(self) -> None:
        expected = build_baseline_report(BASELINE_CONFIG)
        actual = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        safety = actual["metrics"]["safety"]
        self.assertEqual(set(safety), {"drug_name_accuracy", "dosage_accuracy", "diacritics_accuracy"})

    def test_exported_bundle_corrects_one_fixture_sentence_with_injected_generator(self) -> None:
        row = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapter = root / "adapter"
            adapter.mkdir()
            (adapter / "darag_variant.json").write_text(
                json.dumps({"variant": "full", "use_retrieval": True}), encoding="utf-8"
            )
            datastore = root / "datastore.json"
            datastore.write_text("[]", encoding="utf-8")
            bundle = root / "bundle"
            subprocess.run(
                [
                    sys.executable,
                    "scribe/training/scripts/export_serve.py",
                    "--adapter-dir",
                    str(adapter),
                    "--datastore",
                    str(datastore),
                    "--output",
                    str(bundle),
                ],
                cwd=ROOT,
                check=True,
            )
            manifest = json.loads((bundle / "serve_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "carepath.gec.serve/1")
            llm = LocalGecLLM(
                bundle,
                OfflineClinicalLLM(),
                generate_fn=lambda _prompt: row["gold_text"] + " <|im_end|>",
            )
            result = llm.correct_transcript(
                row["raw_asr"],
                [RetrievedTerm(term="metformin", score=1.0, category="drug", source="fixture")],
            )
            self.assertEqual(result.corrected_text, row["gold_text"])


if __name__ == "__main__":
    unittest.main()
