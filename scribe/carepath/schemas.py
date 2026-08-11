from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - only used before runtime deps are installed
    class _Field:
        def __init__(self, default: Any = None, default_factory: Any = None):
            self.default = default
            self.default_factory = default_factory

        def value(self) -> Any:
            if self.default_factory is not None:
                return self.default_factory()
            return self.default

    def Field(default: Any = None, default_factory: Any = None, **_: Any) -> Any:
        return _Field(default=default, default_factory=default_factory)

    class BaseModel:
        def __init__(self, **data: Any):
            annotations: dict[str, Any] = {}
            for cls in reversed(type(self).__mro__):
                annotations.update(getattr(cls, "__annotations__", {}))
            for name in annotations:
                if name in data:
                    value = data[name]
                else:
                    default = getattr(type(self), name, None)
                    value = default.value() if isinstance(default, _Field) else default
                setattr(self, name, value)

        def model_dump(self) -> dict[str, Any]:
            return dict(self.__dict__)


class HealthResponse(BaseModel):
    status: str
    app_env: str
    asr_provider: str
    llm_provider: str
    asr_ready: bool
    llm_ready: bool
    details: dict[str, Any] = Field(default_factory=dict)


class CorrectionRequest(BaseModel):
    raw_transcript: str = Field(min_length=1)
    encounter_context: str | None = None


class CorrectionResponse(BaseModel):
    raw_transcript: str
    corrected_transcript: str
    retrieved_terms: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class SoapNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    missing_information: list[str] = Field(default_factory=list)
    review_required: bool = True


class PatientSummary(BaseModel):
    """Plain-language after-visit summary written for the patient, in English.

    Every field must be grounded in what was actually said during the visit.
    This is a record of the consultation, never advice: ``follow_up`` restates
    the clinician's own instructions rather than adding new ones.
    """

    what_we_discussed: str
    medications: str
    follow_up: str
    allergies_noted: list[str] = Field(default_factory=list)
    review_required: bool = True


class SoapNoteResponse(BaseModel):
    id: str
    raw_transcript: str
    corrected_transcript: str
    retrieved_terms: list[str]
    soap: SoapNote
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=800)
    lang: str = "vi"


class VisitNoteResponse(BaseModel):
    """Both documents produced at the end of a bilingual visit.

    ``unconfirmed_turn_count`` is reported rather than hidden: turns the
    clinician never confirmed contribute their original speech to the note, not
    their machine translation, and the count says how many.
    """

    visit_id: str
    turn_count: int
    unconfirmed_turn_count: int
    clinical_note: SoapNote
    patient_summary: PatientSummary
    metadata: dict[str, Any] = Field(default_factory=dict)
