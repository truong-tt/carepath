import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import desc
from sqlmodel import Field, Session, SQLModel, select


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid4().hex


class SessionRecord(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=new_id, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    status: str = "active"
    consent_json: str
    privacy_mode: int = 1
    escalated_at: datetime | None = None


class TurnRecord(SQLModel, table=True):
    __tablename__ = "turns"

    id: str = Field(default_factory=new_id, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    seq: int
    speaker: str
    src_lang: str
    tgt_lang: str
    source_text: str
    normalized_text: str
    translation: str
    asr_confidence: float
    mt_confidence: float
    risk_tier: str
    risk_spans_json: str = "[]"
    readback_json: str | None = None
    status: str
    corrected_text: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class FeedbackRecord(SQLModel, table=True):
    __tablename__ = "feedback"

    id: str = Field(default_factory=new_id, primary_key=True)
    turn_id: str = Field(foreign_key="turns.id", index=True)
    reason: str
    comment: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


def create_session(db: Session, consent: dict[str, Any]) -> SessionRecord:
    session = SessionRecord(consent_json=json.dumps(consent, ensure_ascii=False))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> SessionRecord | None:
    return db.get(SessionRecord, session_id)


def require_session(db: Session, session_id: str) -> SessionRecord:
    session = get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


def list_turns(db: Session, session_id: str) -> list[TurnRecord]:
    return list(
        db.exec(
            select(TurnRecord)
            .where(TurnRecord.session_id == session_id)
            .order_by(TurnRecord.seq)
        )
    )


def next_seq(db: Session, session_id: str) -> int:
    latest = db.exec(
        select(TurnRecord)
        .where(TurnRecord.session_id == session_id)
        .order_by(desc(TurnRecord.seq))
        .limit(1)
    ).first()
    return 1 if latest is None else latest.seq + 1


def create_turn(
    db: Session,
    *,
    session_id: str,
    speaker: str,
    src_lang: str,
    tgt_lang: str,
    source_text: str,
    normalized_text: str,
    translation: str,
    asr_confidence: float,
    mt_confidence: float,
    risk_tier: str,
    risk_spans: list[dict[str, Any]],
    status: str,
    readback: dict[str, Any] | None = None,
) -> TurnRecord:
    session = require_session(db, session_id)
    if session.status == "ended":
        raise HTTPException(status_code=409, detail="session ended")
    turn = TurnRecord(
        session_id=session_id,
        seq=next_seq(db, session_id),
        speaker=speaker,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        source_text=source_text,
        normalized_text=normalized_text,
        translation=translation,
        asr_confidence=asr_confidence,
        mt_confidence=mt_confidence,
        risk_tier=risk_tier,
        risk_spans_json=json.dumps(risk_spans, ensure_ascii=False),
        readback_json=json.dumps(readback, ensure_ascii=False) if readback else None,
        status=status,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def confirm_turn(db: Session, turn_id: str, edited_translation: str | None) -> TurnRecord:
    turn = db.get(TurnRecord, turn_id)
    if turn is None:
        raise HTTPException(status_code=404, detail="turn not found")
    session = require_session(db, turn.session_id)
    if session.status == "ended":
        raise HTTPException(status_code=409, detail="session ended")
    if turn.status not in {"awaiting_confirm", "blocked"}:
        raise HTTPException(status_code=409, detail="turn is not awaiting confirmation")
    turn.status = "corrected" if edited_translation else "confirmed"
    turn.corrected_text = edited_translation
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def create_feedback(
    db: Session,
    turn_id: str,
    reason: str,
    comment: str | None,
) -> FeedbackRecord:
    if db.get(TurnRecord, turn_id) is None:
        raise HTTPException(status_code=404, detail="turn not found")
    feedback = FeedbackRecord(turn_id=turn_id, reason=reason, comment=comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def end_session(db: Session, session_id: str) -> None:
    session = require_session(db, session_id)
    session.status = "ended"
    db.add(session)
    db.commit()


def escalate_session(db: Session, session_id: str) -> None:
    session = require_session(db, session_id)
    session.status = "escalated"
    session.escalated_at = utc_now()
    db.add(session)
    db.commit()


def hard_delete_session(db: Session, session_id: str) -> None:
    session = require_session(db, session_id)
    turn_ids = [turn.id for turn in list_turns(db, session_id)]
    for feedback in db.exec(select(FeedbackRecord).where(FeedbackRecord.turn_id.in_(turn_ids))):
        db.delete(feedback)
    for turn in db.exec(select(TurnRecord).where(TurnRecord.session_id == session_id)):
        db.delete(turn)
    db.delete(session)
    db.commit()
