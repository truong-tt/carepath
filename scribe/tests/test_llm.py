from __future__ import annotations

import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from carepath.config import Settings
from carepath.services.llm import (
    FallbackClinicalLLM,
    LLMError,
    OfflineClinicalLLM,
    OpenAICompatibleLLM,
    _can_retry_without_response_format,
    extract_json_object,
    normalize_transcript_spacing,
)
from carepath.services.retrieval import RetrievedTerm


class _BrokenLLM:
    """Primary provider that always fails, to exercise the offline fallback."""

    provider_name = "ckey"

    def readiness(self):
        return False, {"provider": self.provider_name, "broken": True}

    def correct_transcript(self, raw_text, retrieved_terms, encounter_context=None):
        raise LLMError("simulated provider outage")

    def generate_soap(self, corrected_text, retrieved_terms, encounter_context=None):
        raise LLMError("simulated provider outage")

    def generate_patient_summary(self, transcript_en, retrieved_terms, encounter_context=None):
        raise LLMError("simulated provider outage")


def make_settings(**overrides) -> Settings:
    """Settings is a plain dataclass, so every field has to be supplied."""
    defaults = dict(
        app_env="test",
        asr_provider="mock",
        allow_mock_asr=True,
        gipformer_quantize="int8",
        gipformer_num_threads=1,
        gipformer_decoding_method="modified_beam_search",
        gipformer_chunk_seconds=20.0,
        gipformer_segmentation="overlap",
        gipformer_overlap_seconds=2.0,
        gipformer_max_segment_seconds=20.0,
        gipformer_vad_model=None,
        llm_provider="ckey",
        llm_base_url="https://api.xah.io/v1",
        llm_model="gpt-5.4",
        llm_api_key="sk-test",
        llm_timeout_seconds=1,
        medical_lexicon_path=Path("data/medical_lexicon.json"),
        retrieval_top_k=5,
        retrieval_backend="lexical",
        semantic_model_name="bkai-foundation-models/vietnamese-bi-encoder",
    )
    return Settings(**{**defaults, **overrides})


# Speaker-per-line, exactly as the visit bridge renders it.
VISIT_TRANSCRIPT_EN = "\n".join(
    [
        "Patient: I developed a rash after taking amoxicillin",
        "Patient: I was taking 500 milligrams twice a day",
        "Clinician: I will stop this medicine and prescribe a different one",
    ]
)


class PatientSummaryTests(unittest.TestCase):
    def test_offline_summary_is_grounded_in_the_transcript(self) -> None:
        result = OfflineClinicalLLM().generate_patient_summary(VISIT_TRANSCRIPT_EN, [])
        summary = result.summary

        self.assertEqual(result.provider, "offline")
        self.assertTrue(summary.review_required)
        self.assertIn("amoxicillin", summary.what_we_discussed)
        # A patient says "500 milligrams", not "500 mg".
        self.assertIn("500 milligrams", summary.medications)
        self.assertTrue(any("amoxicillin" in item for item in summary.allergies_noted))

    def test_offline_summary_keeps_each_turn_a_separate_clause(self) -> None:
        """Speaker lines must not fuse: one allergy note, not the whole visit."""
        summary = OfflineClinicalLLM().generate_patient_summary(VISIT_TRANSCRIPT_EN, []).summary

        self.assertTrue(summary.allergies_noted)
        for item in summary.allergies_noted:
            self.assertNotIn("Clinician:", item)
            self.assertNotIn("stop this medicine", item)

    def test_offline_summary_invents_no_drug(self) -> None:
        summary = OfflineClinicalLLM().generate_patient_summary(VISIT_TRANSCRIPT_EN, []).summary
        combined = " ".join(
            [summary.what_we_discussed, summary.medications, summary.follow_up]
        ).lower()
        self.assertNotIn("paracetamol", combined)
        self.assertNotIn("ibuprofen", combined)

    def test_offline_summary_handles_an_empty_visit(self) -> None:
        summary = OfflineClinicalLLM().generate_patient_summary("", []).summary
        self.assertIn("No conversation", summary.what_we_discussed)
        self.assertIn("No medication", summary.medications)
        self.assertEqual(summary.allergies_noted, [])

    def test_network_summary_parses_a_valid_response(self) -> None:
        provider = OpenAICompatibleLLM(make_settings())
        payload = (
            '{"what_we_discussed": "You reported a rash after amoxicillin.",'
            ' "medications": "Amoxicillin 500 mg twice a day was stopped.",'
            ' "follow_up": "Return if the rash spreads.",'
            ' "allergies_noted": ["amoxicillin"], "review_required": false}'
        )
        with patch.object(provider, "_chat_json", return_value=payload):
            result = provider.generate_patient_summary(VISIT_TRANSCRIPT_EN, [])

        self.assertEqual(result.summary.allergies_noted, ["amoxicillin"])
        self.assertTrue(
            result.summary.review_required,
            "review_required must never be turned off by the model",
        )

    def test_network_summary_missing_fields_raise_llm_error(self) -> None:
        provider = OpenAICompatibleLLM(make_settings())
        with patch.object(provider, "_chat_json", return_value='{"what_we_discussed": "hi"}'):
            with self.assertRaises(LLMError):
                provider.generate_patient_summary(VISIT_TRANSCRIPT_EN, [])

    def test_fallback_serves_offline_summary_when_primary_fails(self) -> None:
        provider = FallbackClinicalLLM(_BrokenLLM(), OfflineClinicalLLM())
        result = provider.generate_patient_summary(VISIT_TRANSCRIPT_EN, [])

        self.assertEqual(result.provider, "offline_fallback")
        self.assertIn("amoxicillin", result.summary.what_we_discussed)


class LLMTests(unittest.TestCase):
    def test_extract_json_object_from_fenced_response(self) -> None:
        parsed = extract_json_object('```json\n{"corrected_transcript":"abc"}\n```')
        self.assertEqual(parsed["corrected_transcript"], "abc")

    def test_normalize_transcript_spacing(self) -> None:
        self.assertEqual(normalize_transcript_spacing("  SpO2   98 % "), "SpO2 98%")

    def test_offline_provider_preserves_units_and_review_required(self) -> None:
        provider = OfflineClinicalLLM()
        terms = [RetrievedTerm(term="SpO2", score=1.0, category="vital_sign", source="spo2")]
        correction = provider.correct_transcript(
            "bệnh nhân đau ngực spo2 98 % huyết áp 120 trên 80 mmhg",
            terms,
        )
        self.assertIn("SpO2", correction.corrected_text)
        self.assertIn("mmHg", correction.corrected_text)
        soap_result = provider.generate_soap(correction.corrected_text, terms)
        self.assertEqual(soap_result.provider, "offline")
        soap = soap_result.soap
        self.assertTrue(soap.review_required)
        self.assertIn("đau", soap.subjective.lower())

    def test_offline_soap_distributes_clauses_across_sections(self) -> None:
        llm = OfflineClinicalLLM()
        text = (
            "Bệnh nhân đau ngực, huyết áp 150 trên 90 mmHg, "
            "nghĩ đến hội chứng vành cấp, cho làm ECG và troponin."
        )
        soap = llm.generate_soap(text, []).soap
        self.assertIn("đau ngực", soap.subjective)
        self.assertIn("mmHg", soap.objective)
        self.assertIn("hội chứng vành cấp", soap.assessment)
        self.assertIn("ECG", soap.plan)
        # the chief complaint must not leak into objective (the old bug)
        self.assertNotIn("đau ngực", soap.objective)

    def test_fallback_serves_offline_when_primary_fails(self) -> None:
        llm = FallbackClinicalLLM(_BrokenLLM(), OfflineClinicalLLM())
        terms = [RetrievedTerm(term="SpO2", score=1.0, category="vital_sign", source="spo2")]

        correction = llm.correct_transcript(
            "benh nhan dau nguc spo2 98 % huyet ap 120 tren 80 mmhg", terms
        )
        self.assertEqual(correction.provider, "offline_fallback")
        self.assertIn("SpO2", correction.corrected_text)

        soap_result = llm.generate_soap(correction.corrected_text, terms)
        self.assertEqual(soap_result.provider, "offline_fallback")
        self.assertTrue(soap_result.soap.review_required)

    def test_can_retry_without_response_format_for_provider_errors(self) -> None:
        self.assertTrue(_can_retry_without_response_format(400, "unknown response_format"))
        self.assertTrue(_can_retry_without_response_format(422, "json_object unsupported"))
        self.assertFalse(_can_retry_without_response_format(401, "response_format"))

    def test_ckey_provider_retries_without_response_format(self) -> None:
        # Only reachable with the hint opted in; it is off by default because
        # CKey's gpt-5.4 hangs on it rather than returning a 400.
        provider = OpenAICompatibleLLM(make_settings(llm_json_response_format=True))
        calls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return (
                    b'{"choices":[{"message":{"content":"{\\"corrected_transcript\\":'
                    b'\\"ok\\"}"}}]}'
                )

        def fake_urlopen(request, timeout):
            calls.append(request.data.decode("utf-8"))
            if len(calls) == 1:
                raise urllib.error.HTTPError(
                    request.full_url,
                    400,
                    "Bad Request",
                    hdrs=None,
                    fp=_BytesReader(b'{"error":"response_format unsupported"}'),
                )
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            content = provider._chat_json("system", "user")

        self.assertEqual(content, '{"corrected_transcript":"ok"}')
        self.assertIn("response_format", calls[0])
        self.assertNotIn("response_format", calls[1])

    def test_response_format_is_off_by_default(self) -> None:
        """A gateway hang is not an HTTPError, so the retry cannot rescue it."""
        provider = OpenAICompatibleLLM(make_settings())
        calls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return (
                    b'{"choices":[{"message":{"content":"{\\"corrected_transcript\\":'
                    b'\\"ok\\"}"}}]}'
                )

        def fake_urlopen(request, timeout):
            calls.append(request.data.decode("utf-8"))
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            provider._chat_json("system", "user")

        self.assertEqual(len(calls), 1)
        self.assertNotIn("response_format", calls[0])


class _BytesReader:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def close(self) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
