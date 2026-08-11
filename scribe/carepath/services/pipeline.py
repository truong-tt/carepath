from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from carepath.config import Settings
from carepath.schemas import PatientSummary, SoapNote
from carepath.services.asr import ASRService, build_asr_service
from carepath.services.llm import ClinicalLLM, LLMError, build_llm
from carepath.services.retrieval import RetrievedTerm, TermRetriever, build_retriever

logger = logging.getLogger("carepath.pipeline")


@dataclass(frozen=True)
class PipelineOutput:
    id: str
    raw_transcript: str
    corrected_transcript: str
    retrieved_terms: list[RetrievedTerm]
    soap: SoapNote
    metadata: dict[str, object]


@dataclass(frozen=True)
class VisitOutput:
    id: str
    soap: SoapNote
    patient_summary: PatientSummary
    retrieved_terms: list[RetrievedTerm]
    metadata: dict[str, object]


class CarePathPipeline:
    def __init__(
        self,
        settings: Settings,
        asr: ASRService | None = None,
        llm: ClinicalLLM | None = None,
        retriever: TermRetriever | None = None,
    ):
        self.settings = settings
        self.asr = asr or build_asr_service(settings)
        self.llm = llm or build_llm(settings)
        self.retriever = retriever or build_retriever(settings)

    def health(self) -> dict[str, object]:
        asr_ready, asr_details = self.asr.readiness()
        llm_ready, llm_details = self.llm.readiness()
        return {
            "status": "ok" if asr_ready and llm_ready else "degraded",
            "asr_ready": asr_ready,
            "llm_ready": llm_ready,
            "details": {"asr": asr_details, "llm": llm_details},
        }

    def probe_llm(self) -> dict[str, object]:
        """Call the *primary* LLM directly, bypassing the offline fallback.

        Used by preflight to surface a broken CKey link instead of letting the
        fallback silently mask it. Never raises.
        """

        primary = getattr(self.llm, "primary", self.llm)
        try:
            primary.correct_transcript("kiểm tra kết nối SpO2 98 %", [])
            return {
                "probe": "ok",
                "provider": getattr(primary, "provider_name", "offline"),
            }
        except LLMError as exc:
            return {"probe": "failed", "error": str(exc)}

    def warmup(self, probe_llm: bool = False) -> dict[str, object]:
        """Eagerly load heavy resources (and optionally probe the live LLM).

        Run before a demo so the first real request does not pay the Gipformer
        download/model-load cost.
        """

        report: dict[str, object] = {"asr": self.asr.warmup()}
        if probe_llm:
            report["llm"] = self.probe_llm()
        return report

    def process_audio(
        self, normalized_audio_path: Path, encounter_context: str | None = None
    ) -> PipelineOutput:
        start = time.perf_counter()
        asr_result = self.asr.transcribe(normalized_audio_path)
        logger.info(
            "asr done model=%s chars=%d duration_s=%s",
            asr_result.model,
            len(asr_result.text),
            asr_result.metadata.get("duration_seconds"),
        )
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
        soap_result = self.llm.generate_soap(
            correction.corrected_text,
            retrieved_terms,
            encounter_context=encounter_context,
        )
        soap = soap_result.soap
        soap.review_required = True
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "text pipeline done gec_mode=%s soap_mode=%s terms=%d latency_ms=%d",
            correction.provider,
            soap_result.provider,
            len(retrieved_terms),
            latency_ms,
        )
        return PipelineOutput(
            id=str(uuid.uuid4()),
            raw_transcript=raw_text,
            corrected_transcript=correction.corrected_text,
            retrieved_terms=retrieved_terms,
            soap=soap,
            metadata={
                "gec_mode": correction.provider,
                "soap_mode": soap_result.provider,
                "llm_provider": self.settings.llm_provider,
                "latency_ms": latency_ms,
            },
        )


    def process_visit(
        self,
        clinician_transcript: str,
        patient_transcript: str,
        encounter_context: str | None = None,
    ) -> VisitOutput:
        """Draft both end-of-visit documents from an interpreted consultation.

        Unlike :meth:`process_text` this skips the transcript-correction stage:
        a visit transcript is confirmed human speech and machine translation,
        not raw ASR output, so there are no recognition errors to repair and
        running a correction pass would only risk rewriting clinical text.
        """
        start = time.perf_counter()
        retrieved_terms = self.retriever.retrieve(
            " ".join(part for part in (clinician_transcript, encounter_context) if part),
            self.settings.retrieval_top_k,
        )
        soap_result = self.llm.generate_soap(
            clinician_transcript, retrieved_terms, encounter_context=encounter_context
        )
        soap = soap_result.soap
        soap.review_required = True

        patient_terms = self.retriever.retrieve(patient_transcript, self.settings.retrieval_top_k)
        summary_result = self.llm.generate_patient_summary(
            patient_transcript, patient_terms, encounter_context=encounter_context
        )
        summary = summary_result.summary
        summary.review_required = True

        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "visit pipeline done soap_mode=%s summary_mode=%s terms=%d latency_ms=%d",
            soap_result.provider,
            summary_result.provider,
            len(retrieved_terms),
            latency_ms,
        )
        return VisitOutput(
            id=str(uuid.uuid4()),
            soap=soap,
            patient_summary=summary,
            retrieved_terms=retrieved_terms,
            metadata={
                "soap_mode": soap_result.provider,
                "summary_mode": summary_result.provider,
                "llm_provider": self.settings.llm_provider,
                "latency_ms": latency_ms,
            },
        )


def serialize_terms(terms: list[RetrievedTerm]) -> list[str]:
    return [item.term for item in terms]

