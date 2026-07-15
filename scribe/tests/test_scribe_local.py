from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.config import Settings
from carepath.services.llm import LLMError, build_llm
from carepath.services.retrieval import RetrievedTerm
from carepath.services.scribe_local import LocalScribeLLM


def _bundle(
    root: Path, *, scope: str = "research_only", correction_mode: str = "adapter"
) -> Path:
    adapter_names = ("gec", "soap") if correction_mode == "adapter" else ("soap",)
    for name in adapter_names:
        (root / "adapters" / name).mkdir(parents=True)
    manifest = {
        "schema": "carepath.scribe.bundle/1",
        "usage_scope": scope,
        "promotion_status": "blocked_research_only",
        "base_model": "Qwen/Qwen3-4B-Instruct-2507",
        "adapters": {name: f"adapters/{name}" for name in adapter_names},
        "correction_mode": correction_mode,
    }
    (root / "scribe_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


class LocalScribeTests(unittest.TestCase):
    def test_dual_adapter_flow_is_grounded_and_identifiable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            calls: list[str] = []

            def generate(adapter: str, prompt: str) -> str:
                calls.append(adapter)
                task = json.loads(prompt)["task"]
                if task == "correct_asr_transcript":
                    return "Bệnh nhân dùng metformin 500 mg"
                if task == "extract_grounded_clinical_facts":
                    transcript = "Bệnh nhân dùng metformin 500 mg"
                    span = "dùng metformin 500 mg"
                    start = transcript.index(span)
                    return json.dumps(
                        {
                            "facts": [
                                {
                                    "type": "medication",
                                    "value": "metformin 500 mg",
                                    "negated": False,
                                    "uncertain": False,
                                    "source_span": {
                                        "start": start,
                                        "end": start + len(span),
                                        "text": span,
                                    },
                                }
                            ]
                        }
                    )
                return json.dumps(
                    {
                        "subjective": "metformin 500 mg",
                        "objective": "Chưa có thông tin khách quan.",
                        "assessment": "Chưa có đánh giá trong bản ghi.",
                        "plan": "metformin 500 mg",
                        "missing_information": ["Đánh giá"],
                        "review_required": False,
                    }
                )

            llm = LocalScribeLLM(_bundle(Path(temp)), generate_fn=generate)
            terms = [RetrievedTerm("metformin", 1.0, "drug", "test")]
            correction = llm.correct_transcript("Benh nhan dung metformin 500 mg", terms)
            result = llm.generate_soap(correction.corrected_text, terms)

            self.assertEqual(correction.provider, "scribe_local")
            self.assertEqual(result.provider, "scribe_local")
            self.assertTrue(result.soap.review_required)
            self.assertEqual(calls, ["gec", "soap", "soap"])
            ready, details = llm.readiness()
            self.assertTrue(ready)
            self.assertEqual(details["promotion_status"], "blocked_research_only")
            self.assertEqual(details["fallback"], "disabled")

    def test_unsupported_fact_and_number_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            outputs = iter(
                [
                    json.dumps(
                        {
                            "facts": [
                                {
                                    "type": "medication",
                                    "value": "warfarin 5 mg",
                                    "source_span": {
                                        "start": 0,
                                        "end": 13,
                                        "text": "warfarin 5 mg",
                                    },
                                }
                            ]
                        }
                    )
                ]
            )
            llm = LocalScribeLLM(
                _bundle(Path(temp)), generate_fn=lambda adapter, prompt: next(outputs)
            )
            with self.assertRaises(LLMError):
                llm.generate_soap("Bệnh nhân dùng metformin 500 mg", [])

    def test_writer_cannot_append_text_outside_grounded_fact_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            transcript = "Bác sĩ đánh giá viêm họng"
            span = "viêm họng"
            start = transcript.index(span)
            outputs = iter(
                [
                    json.dumps(
                        {
                            "facts": [
                                {
                                    "type": "assessment",
                                    "value": span,
                                    "negated": False,
                                    "uncertain": False,
                                    "source_span": {
                                        "start": start,
                                        "end": start + len(span),
                                        "text": span,
                                    },
                                }
                            ]
                        }
                    ),
                    json.dumps(
                        {
                            "subjective": "Chưa có thông tin chủ quan.",
                            "objective": "Chưa có thông tin khách quan.",
                            "assessment": "viêm họng; ung thư",
                            "plan": "Chưa có kế hoạch trong bản ghi.",
                            "missing_information": [],
                            "review_required": True,
                        }
                    ),
                ]
            )
            llm = LocalScribeLLM(
                _bundle(Path(temp), correction_mode="identity"),
                generate_fn=lambda adapter, prompt: next(outputs),
            )

            with self.assertRaisesRegex(LLMError, "outside grounded fact values"):
                llm.generate_soap(transcript, [])

    def test_manifest_cannot_claim_promotable_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "research_only"):
                LocalScribeLLM(_bundle(Path(temp), scope="production"))

    def test_soap_only_bundle_declares_identity_correction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            llm = LocalScribeLLM(_bundle(Path(temp), correction_mode="identity"))

            correction = llm.correct_transcript("Giữ nguyên bản ghi", [])
            ready, details = llm.readiness()

            self.assertTrue(ready)
            self.assertEqual(correction.corrected_text, "Giữ nguyên bản ghi")
            self.assertEqual(correction.provider, "scribe_local_identity")
            self.assertEqual(details["adapters"], ["soap"])

    def test_build_llm_requires_explicit_staging_bundle_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _bundle(Path(temp))
            with patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "scribe_local",
                    "SCRIBE_BUNDLE_PATH": temp,
                    "LLM_FALLBACK_OFFLINE": "false",
                },
                clear=True,
            ):
                llm = build_llm(Settings.from_env())
            self.assertIsInstance(llm, LocalScribeLLM)


if __name__ == "__main__":
    unittest.main()
