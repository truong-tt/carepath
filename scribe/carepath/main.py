from __future__ import annotations

import hmac
import json
import logging
import os
import tempfile
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session as InterpreterSession

# Interpreter module (interpreter/): the second CarePath product, served by
# this same process so one deploy covers both. Requires `pip install ./interpreter`.
from app import crud as interpreter_crud
from app.api import api_router as interpreter_api_router
from app.api import turn_payload as interpreter_turn_payload
from app.api import ws_router as interpreter_ws_router
from app.config import get_settings as interpreter_settings
from app.db import get_db as get_interpreter_db
from app.main import interpreter_lifespan
from app.providers import get_providers as get_interpreter_providers
from app.providers.registry import read_document
from app.session import process_text_turn

from carepath.config import Settings, load_settings
from carepath.logging_config import configure_logging
from carepath.schemas import (
    CorrectionRequest,
    CorrectionResponse,
    HealthResponse,
    SoapNoteResponse,
    SpeechRequest,
    VisitNoteResponse,
)
from carepath.services.audio import AudioNormalizationError, normalize_audio
from carepath.services.asr import ASRError
from carepath.services.llm import LLMError
from carepath.services.pipeline import CarePathPipeline, serialize_terms
from carepath.services.tts import TTSError, build_tts


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


InterpreterDBDep = Annotated[InterpreterSession, Depends(get_interpreter_db)]


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


# --- Bilingual visit bridge ------------------------------------------------
# Turns an interpreted consultation (Interpreter module, sessions + turns) into
# the two end-of-visit documents (Scribe module, pipeline). Both halves already
# live in this process, so this is a function call, not a service hop.

# A turn the clinician never confirmed contributes only the speech that was
# actually spoken; its machine translation is withheld from both documents.
UNCONFIRMED_TURN_STATUSES = {"awaiting_confirm", "blocked"}

# Every speaker needs a label in both languages: the fallback is the raw key,
# and "document:" reads as a bug in a document a patient takes home.
SPEAKER_LABELS = {
    "vi": {"doctor": "Bác sĩ", "patient": "Bệnh nhân", "document": "Giấy tờ"},
    "en": {"doctor": "Clinician", "patient": "Patient", "document": "Document"},
}


def _render_visit_transcript(turns: list, language: str) -> tuple[str, int]:
    """Render a visit in one language; returns the transcript and how much was withheld.

    Source text is always usable: it is what a human actually said in their own
    language. A translation is usable only once the clinician has confirmed it,
    or where the pipeline judged the turn low-risk and delivered it directly.
    """
    labels = SPEAKER_LABELS[language]
    lines: list[str] = []
    withheld = 0
    for turn in turns:
        if turn.src_lang.lower().startswith(language):
            text = turn.source_text
        elif turn.status in UNCONFIRMED_TURN_STATUSES:
            withheld += 1
            continue
        else:
            text = turn.corrected_text or turn.translation
        text = (text or "").strip()
        if text:
            lines.append(f"{labels.get(turn.speaker, turn.speaker)}: {text}")
    return "\n".join(lines), withheld


def _visit_encounter_context(session) -> str | None:
    """Build encounter context from the patient details captured at visit start.

    These live inside the existing consent blob, so recording them needed no
    schema change on the Interpreter side.
    """
    try:
        consent = json.loads(session.consent_json or "{}")
    except json.JSONDecodeError:
        return None
    context = consent.get("patient_context")
    if not isinstance(context, dict):
        return None
    parts = []
    if context.get("age"):
        parts.append(f"{context['age']} tuổi")
    if context.get("sex"):
        parts.append(str(context["sex"]))
    if context.get("reason"):
        parts.append(f"lý do khám: {context['reason']}")
    return "Bệnh nhân nước ngoài, " + ", ".join(parts) + "." if parts else None


@lru_cache(maxsize=1)
def get_tts():
    return build_tts(get_settings())


@app.post("/api/v1/speech", include_in_schema=False)
def synthesize_speech(payload: SpeechRequest) -> Response:
    """Speak Vietnamese for the patient-facing side of a visit.

    The browser has no vi-VN voice on a default install, so this is what makes
    the English-patient to Vietnamese-clinician direction audible. Returns WAV
    bytes; the caller falls back to browser speech on any error.
    """
    if payload.lang.lower()[:2] != "vi":
        raise HTTPException(status_code=400, detail="only Vietnamese is synthesized server-side")
    try:
        audio, _ = get_tts().synthesize(payload.text)
    except TTSError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )


ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
MAX_DOCUMENT_BYTES = 12 * 1024 * 1024

# The public demo asks for the scripted document with this header. In `demo`
# mode `read_document` returns canned lines and never looks at the bytes, which
# is honest for a sample the page labels as one and would be a fabrication for a
# visitor's own prescription -- so the header is set only on the sample path.
#
# Accepting it from anyone is safe by construction: it can only make the reply
# LESS capable. It cannot read a real document, it cannot bypass the risk engine
# or the clinician gate (both still run on every line in demo mode), and it
# reveals nothing that is not already published on the page as the sample.
SAMPLE_MODE_HEADER = "x-carepath-sample"


def _document_settings(request: Request):
    """Interpreter settings for this document read, honouring the sample header."""
    settings = interpreter_settings()
    if request.headers.get(SAMPLE_MODE_HEADER) == "1":
        return settings.model_copy(update={"provider_mode": "demo"})
    return settings


@app.post("/api/v1/visits/{visit_id}/documents", include_in_schema=False)
def read_visit_document(
    request: Request,
    visit_id: str,
    db: InterpreterDBDep,
    image: UploadFile = File(...),
) -> list[dict]:
    """Read a photographed Vietnamese medical document into confirmable turns.

    The vision model only transcribes. Every line it returns is then put through
    the same pipeline as spoken turns, so translation, the risk engine, the
    reviewer and the clinician gate all apply to paperwork exactly as they do to
    speech -- which is the point: harm concentrates at medication and discharge,
    and those are on paper.

    The image is held in memory and never written to disk, matching the existing
    raw-audio rule.
    """
    interpreter_crud.require_session(db, visit_id)
    suffix = Path(image.filename or "scan.jpg").suffix.lower()
    content_type = (image.content_type or "").lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload a photo of the document.")

    data = image.file.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=400, detail="Image too large.")
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    settings = _document_settings(request)
    try:
        lines = read_document(settings, data, content_type or "image/jpeg")
    except Exception as exc:
        logger.warning(
            "document read failed error_class=%s mode=%s",
            exc.__class__.__name__,
            settings.provider_mode,
        )
        raise HTTPException(status_code=502, detail="Could not read the document.") from exc

    providers = get_interpreter_providers(settings)
    # ponytail: one translation call per line. Measured ~13s/line on ckey, so a
    # six-line prescription is over a minute; the demo runs on scripted mode
    # where it is instant. Batch all lines into a single MT call if live
    # document reading ever has to be fast.
    turns = [
        process_text_turn(
            db,
            providers,
            settings,
            session_id=visit_id,
            speaker="document",
            lang="vi",
            text=line,
            asr_confidence=1.0,
        )
        for line in lines
    ]
    return [interpreter_turn_payload(turn) for turn in turns]


# A named drug or a dose makes a line a medication instruction. Frequency alone
# does not: "come back in 5 days" carries one and is follow-up advice.
MEDICATION_SPAN_KINDS = {"drug_name", "dose_number"}


def _confirmed_medication_lines(turns: list) -> list[str]:
    """English medication instructions taken verbatim from confirmed documents.

    Deliberately not generated. What a patient is told to swallow should be the
    clinician-confirmed translation of what is printed on their prescription,
    not a model's paraphrase of it -- medication reconciliation is one of the
    moments where limited-English-proficiency patients are most often harmed.

    Unconfirmed lines are excluded here for the same reason they are excluded
    from the note.
    """
    lines: list[str] = []
    for turn in turns:
        if turn.speaker != "document" or turn.status in UNCONFIRMED_TURN_STATUSES:
            continue
        kinds = {span.get("kind") for span in json.loads(turn.risk_spans_json or "[]")}
        if not kinds & MEDICATION_SPAN_KINDS:
            continue
        text = (turn.corrected_text or turn.translation or "").strip()
        if text and text not in lines:
            lines.append(text)
    return lines


@app.post("/api/v1/visits/{visit_id}/note", response_model=VisitNoteResponse)
def create_visit_note(visit_id: str, db: InterpreterDBDep) -> VisitNoteResponse:
    session = interpreter_crud.require_session(db, visit_id)  # 404s if unknown
    turns = interpreter_crud.list_turns(db, visit_id)
    if not turns:
        raise HTTPException(status_code=400, detail="visit has no turns to document")

    clinician_transcript, clinician_withheld = _render_visit_transcript(turns, "vi")
    patient_transcript, patient_withheld = _render_visit_transcript(turns, "en")
    if not clinician_transcript and not patient_transcript:
        raise HTTPException(status_code=400, detail="visit has no confirmed content to document")

    try:
        output = get_pipeline().process_visit(
            clinician_transcript,
            patient_transcript,
            encounter_context=_visit_encounter_context(session),
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    summary = output.patient_summary
    medication_lines = _confirmed_medication_lines(turns)
    if medication_lines:
        summary.medications = "\n".join(medication_lines)

    return VisitNoteResponse(
        visit_id=visit_id,
        turn_count=len(turns),
        unconfirmed_turn_count=max(clinician_withheld, patient_withheld),
        clinical_note=output.soap,
        patient_summary=summary,
        metadata={
            **output.metadata,
            "retrieved_terms": serialize_terms(output.retrieved_terms),
        },
    )


# Serve the public frontend same-origin. Mount the site last so API and
# blocked-path routes take precedence.
_REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIST_DIR = Path(os.getenv("SITE_DIST_DIR") or _REPO_ROOT / "scribe" / "frontend" / "dist")


@app.api_route("/phien-dich-y-khoa", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/phien-dich-y-khoa/", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/phien-dich-y-khoa/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console/", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/console/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def blocked_interpreter_browser_path() -> PlainTextResponse:
    """Explicit 404 for the retired interpreter console.

    The console was deleted once /kham-song-ngu/ replaced it, so these paths
    would 404 anyway; keeping the route makes that deliberate rather than
    incidental for anyone holding an old link.
    """
    return PlainTextResponse("Not Found", status_code=404)


@app.get("/robots.txt", include_in_schema=False)
def space_robots() -> PlainTextResponse:
    """Keep the Space out of search results.

    This host serves the same app as the public site, so indexing it would make
    the two duplicate content and could rank the API host instead. Registered
    before the static mount so it wins over the bundled robots.txt, which names
    the public origin.
    """
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


if SITE_DIST_DIR.is_dir():
    # SPA deep links. Both the trailing-slash and bare forms are registered:
    # without the bare form the request falls through to StaticFiles and 404s,
    # which is what /ghi-chep-lam-sang did on this deploy before.
    @app.get("/ghi-chep-lam-sang", include_in_schema=False)
    @app.get("/ghi-chep-lam-sang/", include_in_schema=False)
    def clinical_notes_page() -> FileResponse:
        return FileResponse(SITE_DIST_DIR / "index.html")

    @app.get("/kham-song-ngu", include_in_schema=False)
    @app.get("/kham-song-ngu/", include_in_schema=False)
    def bilingual_visit_page() -> FileResponse:
        return FileResponse(SITE_DIST_DIR / "index.html")

    @app.get("/thu-nghiem", include_in_schema=False)
    @app.get("/thu-nghiem/", include_in_schema=False)
    def public_demo_page() -> FileResponse:
        """The public demo hub.

        The quota endpoints under /api/demo/* are Vercel functions and do not
        exist on this host, so an upload started here fails. The hub already
        treats a failed call as a failure rather than substituting scripted
        output, which is the behaviour that matters. Registering the route
        anyway keeps a shared link from hard-404ing on whichever host it was
        copied from.
        """
        return FileResponse(SITE_DIST_DIR / "index.html")

    app.mount("/", StaticFiles(directory=SITE_DIST_DIR, html=True), name="site")
else:
    logger.warning("site dist missing at %s; / not served", SITE_DIST_DIR)
