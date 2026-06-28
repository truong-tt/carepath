from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from carepath.config import Settings, load_settings
from carepath.logging_config import configure_logging
from carepath.schemas import (
    CorrectionRequest,
    CorrectionResponse,
    HealthResponse,
    SoapNoteResponse,
)
from carepath.services.audio import AudioNormalizationError, normalize_audio
from carepath.services.asr import ASRError
from carepath.services.llm import LLMError
from carepath.services.pipeline import CarePathPipeline, serialize_terms


configure_logging()

# Upload guardrails: reject oversized or non-audio files up front with a clean
# 400 instead of streaming junk through normalization + ASR.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_AUDIO_SUFFIXES = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".oga",
    ".opus",
    ".webm",
}

app = FastAPI(
    title="CarePath API",
    version="0.1.0",
    description="Vietnamese medical ASR correction and SOAP-note drafting API.",
)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


@lru_cache(maxsize=1)
def get_pipeline() -> CarePathPipeline:
    return CarePathPipeline(get_settings())


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    pipeline_health = get_pipeline().health()
    return HealthResponse(
        status=str(pipeline_health["status"]),
        app_env=settings.app_env,
        asr_provider=settings.asr_provider,
        llm_provider=settings.llm_provider,
        asr_ready=bool(pipeline_health["asr_ready"]),
        llm_ready=bool(pipeline_health["llm_ready"]),
        details=dict(pipeline_health["details"]),
    )


@app.post("/api/v1/corrections", response_model=CorrectionResponse)
def correct_transcript(request: CorrectionRequest) -> CorrectionResponse:
    try:
        output = get_pipeline().process_text(
            request.raw_transcript,
            encounter_context=request.encounter_context,
        )
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return CorrectionResponse(
        raw_transcript=output.raw_transcript,
        corrected_transcript=output.corrected_transcript,
        retrieved_terms=serialize_terms(output.retrieved_terms),
        metadata=output.metadata,
    )


def _validate_audio_upload(audio: UploadFile) -> str:
    """Reject non-audio uploads early; return the suffix to use on disk."""

    suffix = Path(audio.filename or "audio.wav").suffix.lower()
    content_type = (audio.content_type or "").lower()
    if suffix not in ALLOWED_AUDIO_SUFFIXES and not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Upload an audio file "
                f"({', '.join(sorted(ALLOWED_AUDIO_SUFFIXES))})."
            ),
        )
    return suffix or ".wav"


def _save_upload_capped(audio: UploadFile, destination: Path, max_bytes: int) -> None:
    """Stream the upload to disk in chunks, aborting if it exceeds ``max_bytes``."""

    written = 0
    with destination.open("wb") as handle:
        while True:
            chunk = audio.file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Audio file too large (limit {max_bytes // (1024 * 1024)} MB).",
                )
            handle.write(chunk)


# Sync ``def`` (not ``async``): the body does blocking work (ONNX ASR + the LLM
# HTTP call), so FastAPI runs it in a threadpool and the event loop stays free to
# serve health checks and other requests instead of freezing for the whole job.
@app.post("/api/v1/soap-notes", response_model=SoapNoteResponse)
def create_soap_note(
    audio: UploadFile = File(...),
    encounter_context: str | None = Form(default=None),
) -> SoapNoteResponse:
    suffix = _validate_audio_upload(audio)
    try:
        with tempfile.TemporaryDirectory(prefix="carepath_") as temp_dir:
            temp_path = Path(temp_dir)
            uploaded_path = temp_path / f"upload{suffix}"
            normalized_path = temp_path / "normalized.wav"
            _save_upload_capped(audio, uploaded_path, MAX_UPLOAD_BYTES)
            normalize_audio(uploaded_path, normalized_path)
            output = get_pipeline().process_audio(
                normalized_path, encounter_context=encounter_context
            )
    except AudioNormalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ASRError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SoapNoteResponse(
        id=output.id,
        raw_transcript=output.raw_transcript,
        corrected_transcript=output.corrected_transcript,
        retrieved_terms=serialize_terms(output.retrieved_terms),
        soap=output.soap,
        metadata=output.metadata,
    )


# Serve the vanilla frontend (apps/web) same-origin so the tool page can call
# the /api/v1 endpoints with relative paths (no CORS). Mounted last so the API
# routes above take precedence; html=True serves index.html for / and /app/.
WEB_DIR = Path(__file__).resolve().parents[2] / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

