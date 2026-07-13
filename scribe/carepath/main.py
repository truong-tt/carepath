from __future__ import annotations

import hmac
import logging
import os
import tempfile
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# Interpreter module (interpreter/): the second CarePath product, served by
# this same process so one deploy covers both. Requires `pip install ./interpreter`.
from app.api import api_router as interpreter_api_router
from app.api import ws_router as interpreter_ws_router
from app.main import interpreter_lifespan

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
logger = logging.getLogger("carepath.main")

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

HOUR_SECONDS = 60 * 60
DAY_SECONDS = 24 * HOUR_SECONDS
_rate_limit_lock = Lock()
_rate_limit_events: dict[str, list[float]] = {}
_global_rate_limit_events: list[float] = []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


@lru_cache(maxsize=1)
def get_pipeline() -> CarePathPipeline:
    return CarePathPipeline(get_settings())


def _warmup_pipeline() -> None:
    report = get_pipeline().warmup()
    logger.info("pipeline warmup complete %s", report)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _warmup_pipeline()
    async with interpreter_lifespan(app):
        yield


app = FastAPI(
    title="CarePath API",
    version="0.1.0",
    description="Vietnamese medical ASR correction and SOAP-note drafting API.",
    lifespan=lifespan,
)


@app.middleware("http")
async def reject_disallowed_origin(request: Request, call_next):
    settings = get_settings()
    origin = request.headers.get("origin")
    request_host = (
        request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    ).split(",", 1)[0].strip().lower()
    try:
        origin_host = urlsplit(origin).netloc.lower() if origin else ""
    except ValueError:
        origin_host = ""
    same_origin = bool(request_host and origin_host == request_host)
    if (
        settings.cors_origins
        and origin
        and not same_origin
        and origin.rstrip("/") not in settings.cors_origins
    ):
        return PlainTextResponse("Disallowed CORS origin", status_code=400)
    return await call_next(request)


if get_settings().cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(get_settings().cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


# Interpreter routes (/api/health, /api/sessions*, /api/turns*, /api/admin/*,
# /ws/sessions/*). No prefix collision with the scriber's /api/v1/*; registered
# before the static mount at the bottom so API routes always win.
app.include_router(interpreter_api_router)
app.include_router(interpreter_ws_router)


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    pipeline_health = get_pipeline().health()
    # Hide the stack (base_url, model, repo_id live in details) in prod; keep it
    # for local debugging. The frontend never reads details.
    details = {} if settings.app_env == "prod" else dict(pipeline_health["details"])
    return HealthResponse(
        status=str(pipeline_health["status"]),
        app_env=settings.app_env,
        asr_provider=settings.asr_provider,
        llm_provider=settings.llm_provider,
        asr_ready=bool(pipeline_health["asr_ready"]),
        llm_ready=bool(pipeline_health["llm_ready"]),
        details=details,
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


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        forwarded_ip = forwarded_for.split(",", 1)[0].strip()
        if forwarded_ip:
            return forwarded_ip
    return request.client.host if request.client else "unknown"


def _prune(events: list[float], now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    keep_from = next(
        (idx for idx, event in enumerate(events) if event >= cutoff), len(events)
    )
    del events[:keep_from]


def _retry_after(events: list[float], now: float, window_seconds: int) -> int:
    return max(1, int(events[0] + window_seconds - now) + 1)


def _rate_limit_error(message: str, retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={"message": message, "retry_after_seconds": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


def _check_soap_rate_limit(request: Request) -> None:
    settings = get_settings()
    team_code = request.headers.get("x-team-code")
    if (
        settings.team_code
        and team_code
        and hmac.compare_digest(team_code, settings.team_code)
    ):
        return

    now = time.time()
    client_ip = _client_ip(request)
    with _rate_limit_lock:
        events = _rate_limit_events.setdefault(client_ip, [])
        _prune(events, now, DAY_SECONDS)
        _prune(_global_rate_limit_events, now, DAY_SECONDS)

        hourly_events = [event for event in events if event >= now - HOUR_SECONDS]
        if (
            settings.soap_rate_limit_per_ip_hour > 0
            and len(hourly_events) >= settings.soap_rate_limit_per_ip_hour
        ):
            raise _rate_limit_error(
                "Bạn đã đạt giới hạn demo cho địa chỉ này. Vui lòng thử lại sau.",
                _retry_after(hourly_events, now, HOUR_SECONDS),
            )
        if (
            settings.soap_rate_limit_per_ip_day > 0
            and len(events) >= settings.soap_rate_limit_per_ip_day
        ):
            raise _rate_limit_error(
                "Bạn đã đạt giới hạn demo cho địa chỉ này. Vui lòng thử lại sau.",
                _retry_after(events, now, DAY_SECONDS),
            )
        if (
            settings.soap_rate_limit_global_day > 0
            and len(_global_rate_limit_events) >= settings.soap_rate_limit_global_day
        ):
            raise _rate_limit_error(
                "Demo đã đạt giới hạn sử dụng trong ngày. Vui lòng thử lại sau.",
                _retry_after(_global_rate_limit_events, now, DAY_SECONDS),
            )

        events.append(now)
        _global_rate_limit_events.append(now)


# Sync ``def`` (not ``async``): the body does blocking work (ONNX ASR + the LLM
# HTTP call), so FastAPI runs it in a threadpool and the event loop stays free to
# serve health checks and other requests instead of freezing for the whole job.
@app.post("/api/v1/soap-notes", response_model=SoapNoteResponse)
def create_soap_note(
    request: Request,
    audio: UploadFile = File(...),
    encounter_context: str | None = Form(default=None),
) -> SoapNoteResponse:
    _check_soap_rate_limit(request)
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


# Serve the public Scribe frontend same-origin. Interpreter APIs remain
# available for development, but no Interpreter browser bundle is public.
# Mount the site last so API and blocked-path routes take precedence.
_REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIST_DIR = Path(os.getenv("SITE_DIST_DIR") or _REPO_ROOT / "scribe" / "frontend" / "dist")


@app.api_route("/phien-dich-y-khoa", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/phien-dich-y-khoa/", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/phien-dich-y-khoa/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console/", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def blocked_interpreter_browser_path() -> PlainTextResponse:
    return PlainTextResponse("Not Found", status_code=404)


if SITE_DIST_DIR.is_dir():
    @app.get("/ghi-chep-lam-sang/", include_in_schema=False)
    def clinical_notes_page() -> FileResponse:
        return FileResponse(SITE_DIST_DIR / "index.html")

    app.mount("/", StaticFiles(directory=SITE_DIST_DIR, html=True), name="site")
else:
    logger.warning("site dist missing at %s; / not served", SITE_DIST_DIR)
