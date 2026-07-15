from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe" / "training" / "scripts"))

from prepare_public_sources import derive_medev_terms  # noqa: E402
from soap.config import load_config  # noqa: E402
from soap.data import (  # noqa: E402
    load_manifest,
    load_terminology,
    grounded_soap_issues,
    prepare_examples,
    read_source,
    sha256_file,
)
from soap.evaluate import safety_issues  # noqa: E402
from soap.schemas import make_fact, validate_example  # noqa: E402
from soap.teacher import SyntheticTeacher  # noqa: E402
from soap.train import (  # noqa: E402
    _locked_checkpoint,
    _package_versions,
    _qlora_backend,
    _train_qlora,
    train as train_soap,
)

CONFIG = ROOT / "scribe" / "training" / "configs" / "soap-smoke-v1.json"
MANIFEST = ROOT / "scribe" / "training" / "manifests" / "soap-public-synthetic-v1.json"
PUBLIC_MANIFEST = ROOT / "scribe" / "training" / "manifests" / "soap-public-v1.json"
FIXTURE = ROOT / "scribe" / "training" / "soap" / "fixtures" / "soap_smoke_v1.jsonl"
TERMS = ROOT / "shared" / "carepath_shared" / "terms" / "medical_terms.json"
REPORT = ROOT / "scribe" / "training" / "reports" / "soap-smoke-v1.json"


class SoapGovernanceTests(unittest.TestCase):
    def test_manifest_pins_train_only_source_hash_and_research_scope(self) -> None:
        manifest = load_manifest(MANIFEST)
        self.assertEqual(manifest["usage_scope"], "research_only")
        self.assertEqual(manifest["promotion_status"], "blocked_research_only")
        self.assertEqual(manifest["sources"][0]["allowed_splits"], ["train"])
        self.assertEqual(manifest["sources"][0]["sha256"], sha256_file(FIXTURE))

    def test_unapproved_manifest_is_rejected(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["approval_status"] = "pending_owner_approval"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "owner approval"):
                load_manifest(path)

    def test_smoke_profile_is_cpu_mock_and_bounded(self) -> None:
        config = load_config(CONFIG)
        self.assertEqual(config.profile_name, "smoke")
        self.assertEqual(config.trainer, "mock")
        self.assertEqual(config.max_rows, 20)
        self.assertEqual(config.max_steps, 20)
        self.assertEqual(config.seeds, (13,))

    def test_colab_artifact_root_override_does_not_change_source_paths(self) -> None:
        with patch.dict(os.environ, {"CAREPATH_ARTIFACT_ROOT": "D:/carepath-drive"}):
            config = load_config(CONFIG)
        self.assertEqual(config.artifact_root, Path("D:/carepath-drive"))
        self.assertEqual(
            config.sources[0]["path"],
            "scribe/training/soap/fixtures/soap_smoke_v1.jsonl",
        )

    def test_public_adapters_accept_training_rows_and_reject_held_out_splits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mts = root / "mts.csv"
            mts.write_text(
                "id,dialogue,section_text\n1,Patient has cough,Assessment text\n",
                encoding="utf-8",
            )
            aci = root / "aci.jsonl"
            aci.write_text(
                json.dumps(
                    {
                        "encounter_id": "a1",
                        "split": "train",
                        "transcript": "Doctor and patient dialogue",
                        "note": "Clinical note",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(read_source(mts, "mts_dialog")[0]["source_split"], "train")
            self.assertEqual(read_source(aci, "aci_bench")[0]["source_split"], "train")
            aci.write_text(
                json.dumps(
                    {
                        "split": "test",
                        "transcript": "held out dialogue",
                        "note": "held out note",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "refuses non-train"):
                read_source(aci, "aci_bench")

    def test_paid_profiles_pin_approved_public_sources_and_base_revision(self) -> None:
        manifest = load_manifest(PUBLIC_MANIFEST)
        self.assertEqual(manifest["owner_approval"]["scope"], "private_research_only")
        self.assertEqual(
            {source["allowed_splits"][0] for source in manifest["sources"]}, {"train"}
        )
        for profile in ("pilot", "research-full", "replicate"):
            path = ROOT / "scribe" / "training" / "configs" / f"soap-{profile}-v1.json"
            config = load_config(path)
            self.assertEqual(config.profile_name, profile)
            self.assertEqual(config.medev_source_id, "medev-terms")
            self.assertEqual(
                config.medev_terms, Path("/content/carepath_data/medev/terms.csv")
            )
            self.assertEqual(
                config.base_revision, "cdbee75f17c01a7cc42f958dc650907174af0554"
            )

    def test_medev_extract_keeps_only_aligned_canonical_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "terms.json"
            canonical.write_text(
                json.dumps(
                    {
                        "terms": [
                            {
                                "term_vi": "đái tháo đường",
                                "term_en": "Diabetes mellitus",
                            },
                            {"term_vi": "aspirin", "term_en": "aspirin"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            english = root / "train.en.txt"
            english.write_text(
                "Patient has diabetes mellitus.\nAspirin was discussed.\n",
                encoding="utf-8",
            )
            vietnamese = root / "train.vi.txt"
            vietnamese.write_text(
                "Bệnh nhân đái tháo đường.\nKhông bàn thuốc.\n", encoding="utf-8"
            )
            output = root / "terms.csv"
            self.assertEqual(
                derive_medev_terms(english, vietnamese, canonical, output), 1
            )
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "vi,en\nđái tháo đường,diabetes mellitus\n",
            )


class SoapGroundingTests(unittest.TestCase):
    def test_preparation_creates_exact_spans_and_provenance(self) -> None:
        config = load_config(CONFIG)
        rows, rejected = prepare_examples(
            config, load_manifest(MANIFEST), SyntheticTeacher()
        )
        self.assertFalse(rejected)
        self.assertEqual({row["provenance"]["source_split"] for row in rows}, {"train"})
        self.assertEqual({row["split"] for row in rows}, {"train", "validation"})
        for row in rows:
            self.assertFalse(validate_example(row))
            self.assertEqual(len(row["provenance"]["source_row_sha256"]), 64)
            teacher = row["provenance"]["teacher"]
            self.assertEqual(teacher["prompt_version"], "carepath-grounded-soap-v1")
            self.assertEqual(len(teacher["prompt_config_sha256"]), 64)

    def test_source_span_must_match_exact_transcript_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact transcript span"):
            make_fact(
                "Bệnh nhân không sốt.", "symptom", "sốt", "không ho", negated=True
            )

    def test_safety_rejects_invented_medication_dose_assessment_and_negation(
        self,
    ) -> None:
        config = load_config(CONFIG)
        rows, _ = prepare_examples(config, load_manifest(MANIFEST), SyntheticTeacher())
        row = rows[-1]
        prediction = {
            "facts": copy.deepcopy(row["facts"]),
            "soap": copy.deepcopy(row["soap"]),
        }
        prediction["facts"].append(
            make_fact(row["transcript"], "medication", "metformin", "paracetamol")
        )
        prediction["facts"][1]["negated"] = False
        prediction["soap"]["assessment"] = "Tăng huyết áp."
        prediction["soap"]["plan"] += " Metformin 750 mg."
        issues = safety_issues(
            row["transcript"],
            {"facts": row["facts"], "soap": row["soap"]},
            prediction,
            load_terminology(config.canonical_terms),
        )
        self.assertTrue(issues["unsupported_critical"])
        self.assertIn("750mg", issues["numeric_errors"])
        self.assertTrue(issues["negation_errors"])

    def test_silver_data_gate_rejects_writer_inventions_before_training(self) -> None:
        config = load_config(CONFIG)
        rows, _ = prepare_examples(config, load_manifest(MANIFEST), SyntheticTeacher())
        row = copy.deepcopy(rows[0])
        row["soap"]["plan"] += "; metformin; 750 mg"
        row["soap"]["assessment"] = "đái tháo đường"
        issues = grounded_soap_issues(row, load_terminology(config.canonical_terms))
        self.assertTrue(any("numbers/units" in issue for issue in issues))
        self.assertTrue(any("unsupported fact text" in issue for issue in issues))
        self.assertTrue(any("unsupported medication" in issue for issue in issues))
        self.assertTrue(any("unsupported assessment" in issue for issue in issues))


class SoapTrainingBackendTests(unittest.TestCase):
    def test_backend_defaults_to_unsloth_and_accepts_only_explicit_choices(
        self,
    ) -> None:
        with patch.dict(os.environ):
            os.environ.pop("CAREPATH_QLORA_BACKEND", None)
            self.assertEqual(_qlora_backend(), "unsloth")
        for backend in ("unsloth", "hf"):
            with patch.dict(os.environ, {"CAREPATH_QLORA_BACKEND": backend}):
                self.assertEqual(_qlora_backend(), backend)
        with patch.dict(os.environ, {"CAREPATH_QLORA_BACKEND": "auto"}):
            with self.assertRaisesRegex(RuntimeError, "exactly 'unsloth' or 'hf'"):
                _qlora_backend()

    def test_missing_unsloth_setup_failure_finalizes_training_run(self) -> None:
        config = load_config(CONFIG)
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"CAREPATH_QLORA_BACKEND": "unsloth"}),
            patch.dict(sys.modules, {"unsloth": None}),
        ):
            output = Path(directory)
            with self.assertRaisesRegex(
                RuntimeError, "requires the 'unsloth' package"
            ):
                _train_qlora(config, output, 13, [], [])
            metadata = json.loads(
                (output / "training_run.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["completion_status"], "failed")
            self.assertEqual(metadata["backend"], "unsloth")
            self.assertIn("RuntimeError", metadata["error"])

    def test_checkpoint_backend_is_locked_and_legacy_means_hf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "checkpoint-20").mkdir()
            expected = str(output / "checkpoint-20")
            self.assertEqual(_locked_checkpoint(output, "hf"), expected)
            with self.assertRaisesRegex(RuntimeError, "'hf' checkpoint.*'unsloth'"):
                _locked_checkpoint(output, "unsloth")

            (output / "training_run.json").write_text(
                json.dumps({"backend": "unsloth"}), encoding="utf-8"
            )
            self.assertEqual(_locked_checkpoint(output, "unsloth"), expected)
            with self.assertRaisesRegex(RuntimeError, "'unsloth' checkpoint.*'hf'"):
                _locked_checkpoint(output, "hf")

    def test_present_missing_or_malformed_checkpoint_backend_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "checkpoint-20").mkdir()
            (output / "training_run.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                _locked_checkpoint(output, "hf")
            (output / "training_run.json").write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "cannot verify"):
                _locked_checkpoint(output, "hf")

    def test_unsloth_run_records_both_backend_package_versions(self) -> None:
        versions = _package_versions()
        self.assertIn("unsloth", versions)
        self.assertIn("unsloth-zoo", versions)

    def test_mock_training_does_not_resolve_or_import_qlora_backend(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = root / "prepared.jsonl"
            prepared.write_text(
                "\n".join(
                    json.dumps({"split": split})
                    for split in ("train", "validation")
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"CAREPATH_QLORA_BACKEND": "invalid"}):
                outputs = train_soap(config, prepared, root / "adapters")
            self.assertEqual(outputs, [root / "adapters" / "seed-13"])
            metadata = json.loads(
                (outputs[0] / "training_run.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["compute_dtype"], "mock")


class SoapPipelineSmokeTests(unittest.TestCase):
    def test_exact_approved_cli_command_exports_blocked_research_bundle(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            config["artifact_root"] = directory
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            env = dict(os.environ)
            result = subprocess.run(
                [
                    sys.executable,
                    "scribe/training/scripts/run_soap_pipeline.py",
                    "--config",
                    str(path),
                    "--stage",
                    "all",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run_root = Path(directory) / config["run_id"]
            report = json.loads(
                (run_root / "evaluation.json").read_text(encoding="utf-8")
            )
            self.assertTrue(report["gate"]["accepted"])
            self.assertEqual(
                report["systems"]["adapter"]["unsupported_critical_facts"], 0
            )
            self.assertEqual(
                set(report["systems"]["adapter"]["demographic_slices"]["groups"]),
                {"age_group", "gender"},
            )
            baseline = json.loads(REPORT.read_text(encoding="utf-8"))
            self.assertEqual(baseline["fixture_sha256"], sha256_file(FIXTURE))
            self.assertEqual(
                report["gate"]["accepted"], baseline["expected"]["gate_accepted"]
            )
            for system, expected in baseline["expected"]["systems"].items():
                for metric, value in expected.items():
                    self.assertEqual(report["systems"][system][metric], value)
            teacher_label = baseline["expected"]["teacher_label"]
            self.assertEqual(
                report["system_provenance"][teacher_label]["comparison"],
                baseline["expected"]["teacher_comparison"],
            )
            bundle = json.loads(
                (run_root / "bundle" / "scribe_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(bundle["usage_scope"], "research_only")
            self.assertEqual(bundle["promotion_status"], "blocked_research_only")
            self.assertEqual(bundle["adapters"], {"soap": "adapters/soap"})
            self.assertEqual(bundle["correction_mode"], "identity")
            self.assertTrue((run_root / "bundle" / "adapters" / "soap").is_dir())
            self.assertIn("soap", bundle["prompts"])
            self.assertEqual(bundle["max_new_tokens"]["soap"], 1200)
            self.assertEqual(
                bundle["tasks"], ["extract_grounded_facts", "write_grounded_soap"]
            )
            stage = subprocess.run(
                [
                    sys.executable,
                    "scribe/training/scripts/stage_scribe_bundle.py",
                    "--bundle",
                    str(run_root / "bundle"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(stage.returncode, 0)
            self.assertIn("mock soap adapter", (stage.stderr + stage.stdout).lower())
            publish = subprocess.run(
                [
                    sys.executable,
                    "scribe/training/scripts/publish_scribe_bundle.py",
                    "--bundle",
                    str(run_root / "bundle"),
                    "--repo-id",
                    "owner/private-research",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(publish.returncode, 0)
            self.assertIn("confirm-private-upload", publish.stderr + publish.stdout)

            real = Path(directory) / "real-bundle"
            shutil.copytree(run_root / "bundle", real)
            adapter = real / "adapters" / "soap"
            (adapter / "adapter_model.mock.json").unlink()
            adapter_config = json.loads(
                (adapter / "adapter_config.json").read_text(encoding="utf-8")
            )
            adapter_config["peft_type"] = "LORA"
            (adapter / "adapter_config.json").write_text(
                json.dumps(adapter_config), encoding="utf-8"
            )
            (adapter / "training_run.json").write_text(
                json.dumps({"device": "T4 test fixture", "compute_dtype": "float16"}),
                encoding="utf-8",
            )
            (adapter / "adapter_model.safetensors").write_bytes(b"test-only")
            real_manifest_path = real / "scribe_manifest.json"
            real_manifest = json.loads(real_manifest_path.read_text(encoding="utf-8"))
            real_manifest["base_revision"] = "a" * 40
            real_manifest["tokenizer_revision"] = "a" * 40
            real_manifest["files"] = {
                str(item.relative_to(real)).replace("\\", "/"): hashlib.sha256(
                    item.read_bytes()
                ).hexdigest()
                for item in sorted(real.rglob("*"))
                if item.is_file() and item != real_manifest_path
            }
            real_manifest_path.write_text(json.dumps(real_manifest), encoding="utf-8")
            asr_component = Path(directory) / "asr-component"
            asr_component.mkdir()
            (asr_component / "adapter_model.safetensors").write_bytes(b"asr-test-only")
            (asr_component / "tokenizer.json").write_text("{}", encoding="utf-8")
            (asr_component / "metrics.json").write_text(
                json.dumps({"hard_wer": 0.1, "pier": 0.05}), encoding="utf-8"
            )
            (asr_component / "staging_evidence.json").write_text(
                json.dumps({"status": "passed", "real_gpu": True}), encoding="utf-8"
            )
            asr_files = {
                item.name: hashlib.sha256(item.read_bytes()).hexdigest()
                for item in asr_component.iterdir()
                if item.is_file()
            }
            (asr_component / "asr_component.json").write_text(
                json.dumps(
                    {
                        "schema": "carepath.asr.component/1",
                        "usage_scope": "research_only",
                        "gate_accepted": True,
                        "selected_for_serving": True,
                        "model": "test/direct-asr",
                        "revision": "b" * 40,
                        "tokenizer_revision": "b" * 40,
                        "adapter": "adapter_model.safetensors",
                        "tokenizer": "tokenizer.json",
                        "metrics": "metrics.json",
                        "staging_evidence": "staging_evidence.json",
                        "files": asr_files,
                    }
                ),
                encoding="utf-8",
            )
            assembled = Path(directory) / "assembled"
            assembly = subprocess.run(
                [
                    sys.executable,
                    "scribe/training/scripts/assemble_scribe_bundle.py",
                    "--soap-bundle",
                    str(real),
                    "--asr-component",
                    str(asr_component),
                    "--output",
                    str(assembled),
                    "--confirm-stack",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(assembly.returncode, 0, assembly.stdout + assembly.stderr)
            assembled_manifest = json.loads(
                (assembled / "scribe_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                assembled_manifest["transcript_component"]["kind"], "direct_asr"
            )
            self.assertTrue(
                (
                    assembled / "transcript" / "asr" / "adapter_model.safetensors"
                ).is_file()
            )
            self.assertTrue(
                (assembled / "transcript" / "asr" / "tokenizer.json").is_file()
            )
            self.assertTrue(
                (assembled / "transcript" / "asr" / "metrics.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
