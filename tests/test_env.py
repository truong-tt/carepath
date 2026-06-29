from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from carepath.gec.env import (
    bundle_adapter,
    gpu_report,
    in_colab,
    latest_checkpoint,
    restore_artifacts,
    save_artifacts,
)


class EnvDetectionTests(unittest.TestCase):
    def test_in_colab_is_false_in_this_environment(self) -> None:
        self.assertFalse(in_colab())

    def test_gpu_report_returns_a_string_without_crashing(self) -> None:
        # Must be safe whether or not torch/CUDA is installed.
        self.assertIsInstance(gpu_report(), str)


class CheckpointTests(unittest.TestCase):
    def test_no_checkpoint_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(latest_checkpoint(tmp))

    def test_missing_dir_returns_none(self) -> None:
        self.assertIsNone(latest_checkpoint("/no/such/dir/xyz"))

    def test_latest_checkpoint_picks_highest_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for step in (50, 200, 100):
                (root / f"checkpoint-{step}").mkdir()
            (root / "checkpoint-notanumber").mkdir()  # ignored
            self.assertEqual(Path(latest_checkpoint(root)).name, "checkpoint-200")


class BackupHelperTests(unittest.TestCase):
    def test_local_restore_confirms_present_and_errors_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp) / "have.jsonl"
            present.write_text("x", encoding="utf-8")
            # backup=None => local mode: present file is fine.
            restore_artifacts(None, [str(present)])
            # missing file => clear SystemExit pointing back to Part 1.
            with self.assertRaises(SystemExit):
                restore_artifacts(None, [str(Path(tmp) / "missing.jsonl")])

    def test_save_to_backup_copies_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "metrics.json"
            src.write_text("{}", encoding="utf-8")
            backup = Path(tmp) / "drive"
            backup.mkdir()
            save_artifacts(backup, [str(src)])
            self.assertTrue((backup / "metrics.json").exists())

    def test_save_local_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "metrics.json"
            src.write_text("{}", encoding="utf-8")
            save_artifacts(None, [str(src)])  # should not raise


class BundleAdapterTests(unittest.TestCase):
    def test_bundle_keeps_adapter_files_and_drops_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = Path(tmp) / "qwen3" / "full"
            adapter.mkdir(parents=True)
            (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
            (adapter / "adapter_model.safetensors").write_text("weights", encoding="utf-8")
            (adapter / "darag_variant.json").write_text(
                '{"use_retrieval": true}', encoding="utf-8"
            )
            ckpt = adapter / "checkpoint-50"
            ckpt.mkdir()
            (ckpt / "optimizer.pt").write_text("big", encoding="utf-8")

            dest = Path(tmp) / "share"
            bundle, zip_path = bundle_adapter(adapter, dest, name="carepath-gec")

            self.assertTrue((bundle / "adapter_config.json").exists())
            self.assertTrue((bundle / "darag_variant.json").exists())
            self.assertFalse((bundle / "checkpoint-50").exists())  # training-only
            self.assertIsNotNone(zip_path)
            self.assertTrue(zip_path.exists())

    def test_bundle_errors_without_an_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            with self.assertRaises(SystemExit):
                bundle_adapter(empty, Path(tmp) / "share")


if __name__ == "__main__":
    unittest.main()
