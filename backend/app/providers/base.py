from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ASRResult:
    text: str
    confidence: float


@dataclass(frozen=True, slots=True)
class GlossaryEntry:
    term_vi: str
    term_en: str
    kind: str
    lasa_group: str | None = None


@dataclass(frozen=True, slots=True)
class MTResult:
    text: str
    confidence: float


@dataclass(frozen=True, slots=True)
class CriticalEntity:
    kind: str
    source_text: str
    translated_text: str


@dataclass(frozen=True, slots=True)
class Review:
    back_translation: str
    entities: list[CriticalEntity]
    flags: list[str]


class ProviderOutputError(RuntimeError):
    """Provider returned malformed or unsafe output."""


@runtime_checkable
class ASRProvider(Protocol):
    def transcribe(self, audio: bytes, lang: str) -> ASRResult: ...


@runtime_checkable
class MTProvider(Protocol):
    def translate(
        self,
        text: str,
        src: str,
        tgt: str,
        glossary_hits: list[GlossaryEntry],
    ) -> MTResult: ...


@runtime_checkable
class ReviewerProvider(Protocol):
    def review(self, source: str, translation: str, src: str, tgt: str) -> Review: ...
