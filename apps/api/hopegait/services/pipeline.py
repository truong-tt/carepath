from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from hopegait.config import Settings
from hopegait.schemas import SoapNote
from hopegait.services.asr import ASRService, build_asr_service
from hopegait.services.llm import ClinicalLLM, build_llm
from hopegait.services.retrieval import MedicalTermRetriever, RetrievedTerm


@dataclass(frozen=True)
class PipelineOutput:
    id: str
    raw_transcript: str
    corrected_transcript: str
    retrieved_terms: list[RetrievedTerm]
    soap: SoapNote
    metadata: dict[str, object]


class HopeGaitPipeline:
    def __init__(
        self,
        settings: Settings,
        asr: ASRService | None = None,
        llm: ClinicalLLM | None = None,
        retriever: MedicalTermRetriever | None = None,
    ):
        self.settings = settings
        self.asr = asr or build_asr_service(settings)
        self.llm = llm or build_llm(settings)
        self.retriever = retriever or MedicalTermRetriever(
            settings.medical_lexicon_path, top_k=settings.retrieval_top_k
        )

    def health(self) -> dict[str, object]:
        asr_ready, asr_details = self.asr.readiness()
        llm_ready, llm_details = self.llm.readiness()
        return {
            "status": "ok" if asr_ready and llm_ready else "degraded",
            "asr_ready": asr_ready,
            "llm_ready": llm_ready,
            "details": {"asr": asr_details, "llm": llm_details},
        }

    def process_audio(
        self, normalized_audio_path: Path, encounter_context: str | None = None
    ) -> PipelineOutput:
        start = time.perf_counter()
        asr_result = self.asr.transcribe(normalized_audio_path)
        output = self.process_text(asr_result.text, encounter_context)
        metadata = {
            **output.metadata,
            "asr_model": asr_result.model,
            "asr": asr_result.metadata,
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
        return PipelineOutput(
            id=output.id,
            raw_transcript=output.raw_transcript,
            corrected_transcript=output.corrected_transcript,
            retrieved_terms=output.retrieved_terms,
            soap=output.soap,
            metadata=metadata,
        )

    def process_text(
        self, raw_text: str, encounter_context: str | None = None
    ) -> PipelineOutput:
        start = time.perf_counter()
        retrieval_text = " ".join(part for part in (raw_text, encounter_context) if part)
        retrieved_terms = self.retriever.retrieve(retrieval_text, self.settings.retrieval_top_k)
        correction = self.llm.correct_transcript(
            raw_text, retrieved_terms, encounter_context=encounter_context
        )
        soap = self.llm.generate_soap(
            correction.corrected_text,
            retrieved_terms,
            encounter_context=encounter_context,
        )
        soap.review_required = True
        return PipelineOutput(
            id=str(uuid.uuid4()),
            raw_transcript=raw_text,
            corrected_transcript=correction.corrected_text,
            retrieved_terms=retrieved_terms,
            soap=soap,
            metadata={
                "gec_mode": correction.provider,
                "llm_provider": self.settings.llm_provider,
                "latency_ms": int((time.perf_counter() - start) * 1000),
            },
        )


def serialize_terms(terms: list[RetrievedTerm]) -> list[str]:
    return [item.term for item in terms]

