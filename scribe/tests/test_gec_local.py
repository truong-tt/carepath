"""Local GEC serving provider (LLM_PROVIDER=gec_local), GPU-free.

Uses an injected ``generate_fn`` so the model never loads — we test the parts
that bite in production: DARAG prompt assembly from the bundle manifest, the
clinical safety gate, fallback-to-offline on bad output, SOAP delegation, and
the build_llm wiring.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.config import Settings
from carepath.services.gec_local import LocalGecLLM
from carepath.services.llm import FallbackClinicalLLM, LLMError, OfflineClinicalLLM, build_llm
from carepath.services.retrieval import RetrievedTerm

IM_END = "<|im_end|>"


def _bundle(tmp: Path) -> Path:
    (tmp / "adapter").mkdir(parents=True)
    manifest = {
        "schema": "carepath.gec.serve/1",
        "base_model": "Qwen/Qwen3-4B-Instruct-2507",
        "variant": "full",
        "use_retrieval": True,
        "max_new_tokens": 64,
        "adapter_dir": "adapter",
        "datastore": "term_datastore.json",
        "prompt": {
            "system": "You correct Vietnamese medical ASR transcripts.",
            "im_start": "<|im_start|>",
            "im_end": IM_END,
            "best_label": "Best hypothesis: ",
            "others_label": "Other hypotheses:",
            "entities_label": "Named entities: ",
        },
    }
    (tmp / "serve_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp


def _terms() -> list[RetrievedTerm]:
    return [RetrievedTerm(term="testosterone", score=0.91, category="biomarker", source="lexicon")]


class GecLocalTests(unittest.TestCase):
    def test_prompt_assembly_and_strip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            seen = {}

            def fake_gen(prompt: str) -> str:
                seen["prompt"] = prompt
                return f"lượng testosterone cao {IM_END} <trailing junk>"

            llm = LocalGecLLM(_bundle(Path(d)), OfflineClinicalLLM(), generate_fn=fake_gen)
            result = llm.correct_transcript("luong testo cao", _terms())
            self.assertEqual(result.provider, "gec_local")
            self.assertEqual(result.corrected_text, "lượng testosterone cao")  # stripped at im_end
            # prompt carries system, best hypothesis, and the retrieved NE
            self.assertIn("You correct Vietnamese", seen["prompt"])
            self.assertIn("Best hypothesis: luong testo cao", seen["prompt"])
            self.assertIn("Named entities: testosterone", seen["prompt"])
            self.assertTrue(seen["prompt"].endswith("<|im_start|>assistant\n"))

    def test_safety_gate_rejects_empty_and_runaway(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            bundle = _bundle(Path(d))
            empty = LocalGecLLM(bundle, OfflineClinicalLLM(), generate_fn=lambda p: IM_END)
            with self.assertRaises(LLMError):
                empty.correct_transcript("benh nhan do spo2", _terms())
            runaway = LocalGecLLM(
                bundle, OfflineClinicalLLM(), generate_fn=lambda p: ("x " * 50) + IM_END
            )
            with self.assertRaises(LLMError):
                runaway.correct_transcript("benh nhan", _terms())

    def test_fallback_to_offline_on_bad_output(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            primary = LocalGecLLM(_bundle(Path(d)), OfflineClinicalLLM(), generate_fn=lambda p: IM_END)
            wrapped = FallbackClinicalLLM(primary, OfflineClinicalLLM())
            result = wrapped.correct_transcript("benh nhan do spo2", _terms())
            self.assertEqual(result.provider, "offline_fallback")  # degraded, not crashed

    def test_soap_is_delegated(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            llm = LocalGecLLM(_bundle(Path(d)), OfflineClinicalLLM(), generate_fn=lambda p: "x" + IM_END)
            soap = llm.generate_soap("bệnh nhân đau ngực", _terms())
            self.assertEqual(soap.provider, "offline")  # came from the delegate
            self.assertTrue(soap.soap.review_required)

    def test_build_llm_wires_gec_local_with_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            _bundle(Path(d))
            env = {
                "LLM_PROVIDER": "gec_local",
                "GEC_BUNDLE_PATH": d,
                "GEC_SOAP_DELEGATE": "offline",
            }
            old = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                llm = build_llm(Settings.from_env())
            finally:
                for k, v in old.items():
                    os.environ[k] = v if v is not None else ""
                    if v is None:
                        os.environ.pop(k, None)
            self.assertIsInstance(llm, FallbackClinicalLLM)
            ready, details = llm.readiness()
            self.assertEqual(details["provider"], "gec_local")


if __name__ == "__main__":
    unittest.main()
