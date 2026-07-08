import csv
import json
import logging
from dataclasses import dataclass, field
from functools import partial
from io import StringIO
from typing import Annotated, Any

import anyio
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import desc
from sqlmodel import Session as DBSession
from sqlmodel import select

from app import crud
from app.config import Settings, get_settings
from app.db import get_db
from app.providers import get_providers
from app.schemas import (
    ConfirmTurnRequest,
    FeedbackCreateRequest,
    SessionCreateRequest,
    SessionCreateResponse,
)
from app.session import process_audio_turn, process_text_turn

api_router = APIRouter(prefix="/api")
ws_router = APIRouter()
DBDep = Annotated[DBSession, Depends(get_db)]
AdminToken = Annotated[str | None, Header(alias="X-Admin-Token")]
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InFlightTurn:
    speaker: str
    lang: str
    chunks: list[bytes] = field(default_factory=list)


# ponytail: process-local turn lock; use DB/Redis if multi-worker deploy matters.
_in_flight: dict[str, InFlightTurn] = {}


def _risk_spans(turn: crud.TurnRecord) -> list[dict[str, Any]]:
    return json.loads(turn.risk_spans_json or "[]")


def turn_payload(turn: crud.TurnRecord) -> dict[str, Any]:
    return {
        "id": turn.id,
        "session_id": turn.session_id,
        "seq": turn.seq,
        "speaker": turn.speaker,
        "src_lang": turn.src_lang,
        "tgt_lang": turn.tgt_lang,
        "source_text": turn.source_text,
        "normalized_text": turn.normalized_text,
        "translation": turn.translation,
        "asr_confidence": turn.asr_confidence,
        "mt_confidence": turn.mt_confidence,
        "risk_tier": turn.risk_tier,
        "risk_spans": _risk_spans(turn),
        "readback": json.loads(turn.readback_json) if turn.readback_json else None,
        "status": turn.status,
        "corrected_text": turn.corrected_text,
        "created_at": turn.created_at.isoformat(),
    }


def feedback_payload(feedback: crud.FeedbackRecord) -> dict[str, Any]:
    return {
        "id": feedback.id,
        "turn_id": feedback.turn_id,
        "reason": feedback.reason,
        "comment": feedback.comment,
        "created_at": feedback.created_at.isoformat(),
    }


def turn_result_payload(turn: crud.TurnRecord, settings: Settings) -> dict[str, Any]:
    low_confidence = (
        turn.asr_confidence < settings.confidence_threshold
        or turn.mt_confidence < settings.confidence_threshold
    )
    return {
        "type": "turn_result",
        "turn": turn_payload(turn),
        "requires_confirmation": turn.risk_tier in {"high", "critical"}
        or turn.status in {"awaiting_confirm", "blocked"},
        "low_confidence": low_confidence,
    }


async def _send_pipeline_error(websocket: WebSocket, session_id: str, exc: Exception) -> None:
    logger.warning(
        "turn_processing_failed session_id=%s error_class=%s",
        session_id,
        exc.__class__.__name__,
    )
    _in_flight.pop(session_id, None)
    await websocket.send_json(
        {
            "type": "turn_error",
            "message": "translation failed — retry or use typed fallback",
            "retryable": True,
        }
    )


def _session_is_ended(db: DBSession, session_id: str) -> bool:
    return crud.require_session(db, session_id).status == "ended"


async def _send_session_ended(websocket: WebSocket, session_id: str) -> None:
    _in_flight.pop(session_id, None)
    await websocket.send_json(
        {"type": "turn_error", "message": "session ended", "retryable": False}
    )


@api_router.post("/sessions", status_code=201)
def create_session(
    payload: SessionCreateRequest,
    db: DBDep,
) -> SessionCreateResponse:
    session = crud.create_session(db, payload.consent)
    return SessionCreateResponse(session_id=session.id)


@api_router.post("/sessions/{session_id}/end", status_code=204)
def end_session(session_id: str, db: DBDep) -> Response:
    crud.end_session(db, session_id)
    return Response(status_code=204)


@api_router.post("/sessions/{session_id}/escalate", status_code=204)
def escalate_session(session_id: str, db: DBDep) -> Response:
    crud.escalate_session(db, session_id)
    return Response(status_code=204)


@api_router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, db: DBDep) -> Response:
    crud.hard_delete_session(db, session_id)
    return Response(status_code=204)


@api_router.get("/sessions/{session_id}/transcript")
def get_transcript(session_id: str, db: DBDep) -> list[dict[str, Any]]:
    if crud.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")
    return [turn_payload(turn) for turn in crud.list_turns(db, session_id)]


@api_router.post("/turns/{turn_id}/confirm")
def confirm_turn(
    turn_id: str,
    payload: ConfirmTurnRequest,
    db: DBDep,
) -> dict[str, Any]:
    return turn_payload(crud.confirm_turn(db, turn_id, payload.edited_translation))


@api_router.post("/turns/{turn_id}/feedback", status_code=201)
def create_feedback(
    turn_id: str,
    payload: FeedbackCreateRequest,
    db: DBDep,
) -> dict[str, str]:
    feedback = crud.create_feedback(db, turn_id, payload.reason, payload.comment)
    return {"id": feedback.id}


@api_router.get("/admin/review", response_model=None)
def admin_review(
    db: DBDep,
    x_admin_token: AdminToken = None,
    risk: str | None = None,
    flagged: bool = False,
    low_confidence: bool = False,
    escalated: bool = False,
    limit: int = 50,
    offset: int = 0,
    format: str = "json",
) -> dict[str, Any] | Response:
    settings = get_settings()
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="invalid admin token")

    sessions = {session.id: session for session in db.exec(select(crud.SessionRecord))}
    feedback: dict[str, list[crud.FeedbackRecord]] = {}
    for item in db.exec(select(crud.FeedbackRecord)):
        feedback.setdefault(item.turn_id, []).append(item)

    # ponytail: Python scan is enough for single-clinic SQLite MVP.
    rows: list[dict[str, Any]] = []
    for turn in db.exec(select(crud.TurnRecord).order_by(desc(crud.TurnRecord.created_at))):
        turn_feedback = feedback.get(turn.id, [])
        session = sessions.get(turn.session_id)
        if risk and turn.risk_tier != risk:
            continue
        if flagged and not turn_feedback:
            continue
        if low_confidence and (
            turn.asr_confidence >= settings.confidence_threshold
            and turn.mt_confidence >= settings.confidence_threshold
        ):
            continue
        if escalated and session and session.status != "escalated":
            continue
        payload = turn_payload(turn)
        payload["session_status"] = session.status if session else "unknown"
        payload["feedback"] = [feedback_payload(item) for item in turn_feedback]
        rows.append(payload)

    total = len(rows)
    page = rows[offset : offset + limit]
    if format == "csv":
        return review_csv(page)
    return {"items": page, "total": total, "limit": limit, "offset": offset}


def review_csv(rows: list[dict[str, Any]]) -> Response:
    handle = StringIO()
    fieldnames = [
        "id",
        "session_id",
        "speaker",
        "source_text",
        "translation",
        "corrected_text",
        "risk_tier",
        "status",
        "session_status",
        "feedback_reasons",
    ]
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: row.get(key, "")
                for key in fieldnames
                if key != "feedback_reasons"
            }
            | {"feedback_reasons": ";".join(item["reason"] for item in row["feedback"])}
        )
    return Response(content=handle.getvalue(), media_type="text/csv")


@ws_router.websocket("/ws/sessions/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
    db: DBDep,
) -> None:
    try:
        await websocket.accept()
    except RuntimeError:
        return
    settings = get_settings()
    providers = get_providers(settings)
    if crud.get_session(db, session_id) is None:
        await websocket.close(code=1008, reason="session not found")
        return

    await websocket.send_json(
        {
            "type": "session_state",
            "turns": [turn_payload(turn) for turn in crud.list_turns(db, session_id)],
        }
    )

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            if message.get("bytes") is not None:
                current = _in_flight.get(session_id)
                if current is None:
                    await websocket.send_json(
                        {"type": "turn_error", "message": "no turn in progress", "retryable": True}
                    )
                    continue
                current.chunks.append(message["bytes"])
                continue

            event = json.loads(message.get("text") or "{}")
            event_type = event.get("type")
            if event_type in {"start_turn", "end_turn", "text_turn"} and _session_is_ended(
                db, session_id
            ):
                await _send_session_ended(websocket, session_id)
                continue
            if event_type == "start_turn":
                if session_id in _in_flight:
                    await websocket.send_json(
                        {
                            "type": "turn_error",
                            "message": "turn already in progress",
                            "retryable": True,
                        }
                    )
                    continue
                _in_flight[session_id] = InFlightTurn(
                    speaker=event["speaker"],
                    lang=event["lang"],
                )
            elif event_type == "end_turn":
                current = _in_flight.pop(session_id, None)
                if current is None:
                    await websocket.send_json(
                        {"type": "turn_error", "message": "no turn in progress", "retryable": True}
                    )
                    continue
                try:
                    turn = await anyio.to_thread.run_sync(
                        partial(
                            process_audio_turn,
                            db,
                            providers,
                            settings,
                            session_id=session_id,
                            speaker=current.speaker,
                            lang=current.lang,
                            audio=b"".join(current.chunks),
                        )
                    )
                except Exception as exc:
                    await _send_pipeline_error(websocket, session_id, exc)
                    continue
                await websocket.send_json(turn_result_payload(turn, settings))
            elif event_type == "text_turn":
                try:
                    turn = await anyio.to_thread.run_sync(
                        partial(
                            process_text_turn,
                            db,
                            providers,
                            settings,
                            session_id=session_id,
                            speaker=event["speaker"],
                            lang=event["lang"],
                            text=event["text"],
                            asr_confidence=1.0,
                        )
                    )
                except Exception as exc:
                    await _send_pipeline_error(websocket, session_id, exc)
                    continue
                await websocket.send_json(turn_result_payload(turn, settings))
            else:
                await websocket.send_json(
                    {"type": "turn_error", "message": "unknown event type", "retryable": False}
                )
    except WebSocketDisconnect:
        pass
    finally:
        _in_flight.pop(session_id, None)
