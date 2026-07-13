from typing import Any, Literal

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    consent: dict[str, Any]


class SessionCreateResponse(BaseModel):
    session_id: str


class ConfirmTurnRequest(BaseModel):
    edited_translation: str | None = None


class FeedbackCreateRequest(BaseModel):
    reason: Literal["wrong_term", "wrong_meaning", "missing", "other"]
    comment: str | None = Field(default=None, max_length=2000)
