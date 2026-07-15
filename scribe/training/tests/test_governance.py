from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))

from carepath.services.gec_local import LocalGecLLM  # noqa: E402
from carepath.services.llm import OfflineClinicalLLM  # noqa: E402
from carepath.services.retrieval import RetrievedTerm  # noqa: E402
from gec.baseline import build_baseline_report  # noqa: E402
from gec.evaluate import stratified_report, wer_report  # noqa: E402
from gec.manifest import (  # noqa: E402
    load_manifest,
    sha256_file,
    source_lock_sha256,
    split_artifact_fingerprints,
)
from gec.run_config import load_pipeline_config  # noqa: E402

FIXTURE = ROOT / "scribe" / "training" / "eval" / "fixtures" / "gec_eval_v1.jsonl"
FIXTURE_MANIFEST = (
    ROOT / "scribe" / "training" / "eval" / "fixtures" / "gec_eval_v1.manifest.json"
)
BASELINE_CONFIG = ROOT / "scribe" / "training" / "configs" / "frozen-baseline-v1.json"
BASELINE_REPORT = (
    ROOT / "scribe" / "training" / "reports" / "gec-frozen-baseline-v1.json"
)


class DatasetManifestTests(unittest.TestCase):
    def test_frozen_fixture_hash_matches_its_manifest(self) -> None:
        manifest = load_manifest(FIXTURE_MANIFEST)
        self.assertEqual(manifest["sha256"], sha256_file(FIXTURE))

    def test_training_manifest_records_owner_approval_and_immutable_source_lock(
        self,
    ) -> None:
        path = ROOT / "scribe" / "training" / "manifests" / "vimedcss-v1.json"
        manifest = load_manifest(path, require_approved=True)
        self.assertEqual(manifest["dataset_id"], "tensorxt/ViMedCSS")
        self.assertEqual(
            manifest["approved_splits"], ["train", "validation", "test", "hard"]
        )
        self.assertTrue(manifest["training_allowed"])
        self.assertEqual(manifest["owner_approval"]["scope"], "private_research_only")
        self.assertEqual(
            manifest["sha256"],
            source_lock_sha256(
                manifest["dataset_id"],
                manifest["source_revision"],
                manifest["split_fingerprints"],
            ),
        )

    def test_unapproved_copy_is_rejected(self) -> None:
        source = ROOT / "scribe" / "training" / "manifests" / "vimedcss-v1.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["consent_status"] = "pending_owner_approval"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "owner-approved"):
                load_manifest(path, require_approved=True)

    def test_approved_manifest_requires_exact_revision_and_split_fingerprints(
        self,
    ) -> None:
        payload = {
            "dataset_id": "tensorxt/ViMedCSS",
            "source_description": "test",
            "consent_status": "approved_research_only",
            "sha256": "a" * 64,
            "source_revision": "main",
            "split_fingerprints": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact 40-character"):
                load_manifest(path, require_approved=True)

    def test_split_fingerprint_changes_when_a_hub_artifact_changes(self) -> None:
        entries = [
            {
                "type": "file",
                "path": "data/train-00000-of-00001.parquet",
                "size": 10,
                "lfs": {"oid": "a" * 64},
            }
        ]
        first = split_artifact_fingerprints(entries, ("train",))
        entries[0]["lfs"]["oid"] = "b" * 64
        second = split_artifact_fingerprints(entries, ("train",))
        self.assertNotEqual(first, second)

    def test_vietmed_is_approved_for_evaluation_not_training(self) -> None:
        path = ROOT / "scribe" / "training" / "manifests" / "vietmed-test-v1.json"
        manifest = load_manifest(path, require_approved=True)
        self.assertFalse(manifest["training_allowed"])
        self.assertFalse(manifest["retrieval_allowed"])
        self.assertEqual(manifest["approved_splits"], ["test"])


class PipelineConfigTests(unittest.TestCase):
    def test_training_fast_extra_is_pinned_and_not_a_runtime_dependency(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]
        self.assertEqual(
            project["optional-dependencies"]["training-fast"],
            [
                "unsloth==2026.7.2",
                "unsloth-zoo==2026.7.2",
                "transformers==4.56.2",
                "trl==0.22.2",
                "datasets[audio]==4.3.0",
            ],
        )
        runtime = tuple(dependency.lower() for dependency in project["dependencies"])
        for training_only in ("unsloth", "transformers", "trl", "datasets"):
            self.assertFalse(
                any(dependency.startswith(training_only) for dependency in runtime),
                training_only,
            )

    def test_versioned_config_has_fixed_unique_seeds(self) -> None:
        config = load_pipeline_config(
            ROOT / "scribe" / "training" / "configs" / "replicate-v1.json"
        )
        self.assertEqual(config.run_id, "carepath-gec-replicate-v1")
        self.assertEqual(config.profile.seeds, (13, 7, 42))

    def test_duplicate_seeds_are_rejected(self) -> None:
        payload = json.loads(
            (ROOT / "scribe" / "training" / "configs" / "smoke-v2.json").read_text(
                encoding="utf-8"
            )
        )
        payload["profile"]["seeds"] = [13, 13]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique fixed seeds"):
                load_pipeline_config(path)

    def test_profiles_lock_cost_seed_and_synthetic_semantics(self) -> None:
        config_dir = ROOT / "scribe" / "training" / "configs"
        profiles = {
            name: load_pipeline_config(config_dir / filename).profile
            for name, filename in {
                "smoke": "smoke-v2.json",
                "pilot": "pilot-v1.json",
                "research-full": "research-full-v1.json",
                "replicate": "replicate-v1.json",
                "reproduction": "reproduction-v1.json",
            }.items()
        }
        self.assertFalse(profiles["smoke"].paid)
        self.assertEqual(profiles["pilot"].limit_per_split, 1_000)
        self.assertEqual(profiles["research-full"].seeds, (13,))
        self.assertEqual(profiles["replicate"].seeds, (13, 7, 42))
        self.assertFalse(profiles["research-full"].enable_tts)
        self.assertTrue(profiles["reproduction"].enable_tts)
        self.assertFalse(profiles["smoke"].enable_direct_asr)
        self.assertTrue(profiles["pilot"].enable_direct_asr)
        self.assertTrue(profiles["pilot"].enable_phonetic)
        self.assertFalse(profiles["pilot"].enable_near_miss)
        self.assertTrue(profiles["reproduction"].enable_near_miss)
        self.assertIn("not_implemented", profiles["reproduction"].asr_experiment)

    def test_paid_profile_requires_explicit_confirmation(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scribe/training/scripts/run_pipeline.py",
                "--config",
                "scribe/training/configs/pilot-v1.json",
                "--stage",
                "data",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm-paid", result.stderr)

    def test_notebooks_route_fast_extra_and_do_not_embed_secrets(self) -> None:
        result = subprocess.run(
            [sys.executable, "scribe/training/scripts/build_notebooks.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        notebook_dir = ROOT / "scribe" / "training" / "notebooks"
        names = {path.name for path in notebook_dir.glob("[0-9][0-9]_*.ipynb")}
        self.assertEqual(
            names,
            {
                "00_data_prep.ipynb",
                "01_asr_benchmark.ipynb",
                "02_train_gec.ipynb",
                "03_train_soap.ipynb",
                "04_evaluate_export_stage.ipynb",
            },
        )
        fast_notebooks = {"02_train_gec.ipynb", "03_train_soap.ipynb"}
        secret_literal = re.compile(
            r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
            r"hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"
        )
        credential_url = re.compile(r"https?://[^/\s:@]+:[^@\s]+@")
        for path in notebook_dir.glob("[0-9][0-9]_*.ipynb"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            install = "".join(payload["cells"][2]["source"])
            source = "\n".join(
                "".join(cell.get("source", [])) for cell in payload["cells"]
            )
            self.assertIn("PROFILE == 'reproduction'", install)
            self.assertIn("training-tts", install)
            if path.name in fast_notebooks:
                self.assertIn("if PROF.paid:", install)
                self.assertIn("training-fast", install)
            else:
                self.assertNotIn("training-fast", install)
            self.assertFalse(any(cell.get("outputs") for cell in payload["cells"]))
            self.assertIsNone(secret_literal.search(source), path.name)
            self.assertIsNone(credential_url.search(source), path.name)
            self.assertNotIn("x-access-token:{", source)

        bootstrap = (notebook_dir / "00_data_prep.ipynb").read_text(encoding="utf-8")
        self.assertIn("GIT_ASKPASS", bootstrap)
        staging = (notebook_dir / "04_evaluate_export_stage.ipynb").read_text(
            encoding="utf-8"
        )
        self.assertIn("P.root / soap_cfg.run_id / 'bundle'", staging)
        self.assertIn("'replicate' if PROFILE == 'reproduction'", staging)


class StratifiedEvaluationTests(unittest.TestCase):
    def test_frozen_fixture_reports_every_safety_category(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        ]
        report = stratified_report(rows, ["raw_asr"])

        self.assertEqual(
            set(report),
            {"diacritics", "dosage", "drug_name", "laterality", "negation", "numbers"},
        )
        self.assertTrue(
            all(metrics["raw_asr"]["frozen"]["n"] == 2 for metrics in report.values())
        )


class BaselineAndExportTests(unittest.TestCase):
    def test_committed_baseline_matches_the_frozen_fixture(self) -> None:
        expected = build_baseline_report(BASELINE_CONFIG)
        actual = json.loads(BASELINE_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        safety = actual["metrics"]["safety"]
        self.assertEqual(
            set(safety),
            {"drug_name_accuracy", "dosage_accuracy", "diacritics_accuracy"},
        )

    def test_exported_bundle_corrects_one_fixture_sentence_with_injected_generator(
        self,
    ) -> None:
        row = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapter = root / "adapter"
            adapter.mkdir()
            (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
            (adapter / "adapter_model.safetensors").write_bytes(b"test-only")
            (adapter / "base_revision.json").write_text(
                json.dumps(
                    {
                        "model": "Qwen/Qwen3-4B-Instruct-2507",
                        "revision": "a" * 40,
                        "tokenizer_revision": "a" * 40,
                    }
                ),
                encoding="utf-8",
            )
            (adapter / "darag_variant.json").write_text(
                json.dumps({"variant": "full", "use_retrieval": True}), encoding="utf-8"
            )
            datastore = root / "datastore.json"
            datastore.write_text("[]", encoding="utf-8")
            normal_rows = [
                {
                    "split": split,
                    "raw_asr": "uong met pho min",
                    "corrected_text": "uong met pho min",
                    "gec_pred": "uống metformin",
                    "gold_text": "uống metformin",
                    "gold_terms": ["metformin"],
                }
                for split in ("validation", "hard")
            ]
            frozen_rows = [
                {
                    **item,
                    "gec_pred": item["gold_text"],
                }
                for item in (
                    json.loads(line)
                    for line in FIXTURE.read_text(encoding="utf-8").splitlines()
                )
            ]
            normal_report = root / "normal.json"
            frozen_report = root / "frozen.json"
            safety_report = root / "safety.json"
            normal_report.write_text(
                json.dumps(
                    wer_report(normal_rows, ["raw_asr", "corrected_text", "gec_pred"])
                ),
                encoding="utf-8",
            )
            frozen_report.write_text(
                json.dumps(wer_report(frozen_rows, ["raw_asr", "gec_pred"])),
                encoding="utf-8",
            )
            safety_report.write_text(
                json.dumps(stratified_report(frozen_rows, ["raw_asr", "gec_pred"])),
                encoding="utf-8",
            )
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
                    "--normal-gate-report",
                    str(normal_report),
                    "--frozen-gate-report",
                    str(frozen_report),
                    "--frozen-safety-report",
                    str(safety_report),
                ],
                cwd=ROOT,
                check=True,
            )
            manifest = json.loads(
                (bundle / "serve_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema"], "carepath.gec.serve/1")
            self.assertTrue(manifest["gate_accepted"])
            llm = LocalGecLLM(
                bundle,
                OfflineClinicalLLM(),
                generate_fn=lambda _prompt: row["gold_text"] + " <|im_end|>",
            )
            result = llm.correct_transcript(
                row["raw_asr"],
                [
                    RetrievedTerm(
                        term="metformin", score=1.0, category="drug", source="fixture"
                    )
                ],
            )
            self.assertEqual(result.corrected_text, row["gold_text"])


if __name__ == "__main__":
    unittest.main()
