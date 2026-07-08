from collections.abc import Mapping

from app.providers.base import ASRResult, GlossaryEntry, MTResult, Review


class MockASRProvider:
    def __init__(
        self,
        canned: Mapping[tuple[str, str], ASRResult] | None = None,
        *,
        fail: bool = False,
        confidence: float = 0.99,
    ) -> None:
        self.canned = dict(canned or {})
        self.fail = fail
        self.confidence = confidence

    def transcribe(self, audio: bytes, lang: str) -> ASRResult:
        if self.fail:
            raise RuntimeError("mock ASR failure")
        text = audio.decode("utf-8", errors="ignore").strip() or "mock transcript"
        return self.canned.get((lang, text), ASRResult(text=text, confidence=self.confidence))


class MockMTProvider:
    def __init__(
        self,
        canned: Mapping[tuple[str, str, str], MTResult] | None = None,
        *,
        fail: bool = False,
        confidence: float = 0.99,
    ) -> None:
        self.canned = dict(canned or {})
        self.fail = fail
        self.confidence = confidence

    def translate(
        self,
        text: str,
        src: str,
        tgt: str,
        glossary_hits: list[GlossaryEntry],
    ) -> MTResult:
        if self.fail:
            raise RuntimeError("mock MT failure")
        del glossary_hits
        return self.canned.get(
            (src, tgt, text),
            MTResult(text=f"[{src}->{tgt}] {text}", confidence=self.confidence),
        )


class MockReviewerProvider:
    def __init__(
        self,
        canned: Mapping[tuple[str, str, str, str], Review] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.canned = dict(canned or {})
        self.fail = fail

    def review(self, source: str, translation: str, src: str, tgt: str) -> Review:
        if self.fail:
            raise RuntimeError("mock reviewer failure")
        return self.canned.get(
            (src, tgt, source, translation),
            Review(back_translation=source, entities=[], flags=[]),
        )
