import pytest

from app.config import Settings
from app.providers import get_providers
from app.providers.base import ASRProvider, GlossaryEntry, MTProvider, ProviderOutputError
from app.providers.claude_mt import ClaudeMTProvider, parse_mt_output
from app.providers.claude_reviewer import ClaudeReviewerProvider, parse_review_output
from app.providers.openai_asr import OpenAIASRProvider, confidence_from_logprobs


class TextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class Message:
    def __init__(self, text: str) -> None:
        self.content = [TextBlock(text)]


class FakeMessages:
    def __init__(self, text: str) -> None:
        self.text = text
        self.kwargs = {}

    def create(self, **kwargs):
        self.kwargs = kwargs
        return Message(self.text)


class FakeAnthropicClient:
    def __init__(self, text: str) -> None:
        self.messages = FakeMessages(text)


class FakeTranscriptions:
    def __init__(self) -> None:
        self.calls = 0
        self.kwargs = {}

    def create(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        return {"text": "xin chao", "logprobs": [{"logprob": -0.1}, {"logprob": -0.3}]}


class FakeAudio:
    def __init__(self) -> None:
        self.transcriptions = FakeTranscriptions()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.audio = FakeAudio()


def test_registry_returns_cloud_contracts() -> None:
    providers = get_providers(
        Settings(provider_mode="cloud", openai_api_key="openai", anthropic_api_key="anthropic")
    )

    assert isinstance(providers.asr, ASRProvider)
    assert isinstance(providers.mt, MTProvider)


def test_openai_asr_uses_language_hint_and_logprob_confidence() -> None:
    client = FakeOpenAIClient()
    provider = OpenAIASRProvider(api_key="", client=client)

    result = provider.transcribe(b"audio", "vi")

    assert result.text == "xin chao"
    expected_confidence = confidence_from_logprobs([{"logprob": -0.1}, {"logprob": -0.3}])
    assert round(result.confidence, 3) == round(expected_confidence, 3)
    assert client.audio.transcriptions.kwargs["model"] == "gpt-4o-transcribe"
    assert client.audio.transcriptions.kwargs["language"] == "vi"
    assert client.audio.transcriptions.kwargs["include"] == ["logprobs"]


def test_openai_asr_retries_then_raises() -> None:
    class FailingTranscriptions:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **kwargs):
            del kwargs
            self.calls += 1
            raise TimeoutError("slow")

    class FailingClient:
        def __init__(self) -> None:
            self.audio = type("Audio", (), {"transcriptions": FailingTranscriptions()})()

    client = FailingClient()
    provider = OpenAIASRProvider(api_key="", client=client, attempts=2)

    with pytest.raises(RuntimeError, match="ASR transcription failed"):
        provider.transcribe(b"audio", "en")
    assert client.audio.transcriptions.calls == 2


def test_claude_mt_strict_json_and_glossary_prompt() -> None:
    client = FakeAnthropicClient('{"translation":"Take Augmentin after food","confidence":0.93}')
    provider = ClaudeMTProvider(api_key="", client=client)

    result = provider.translate(
        "Uống Augmentin sau ăn",
        "vi",
        "en",
        [GlossaryEntry(term_vi="Augmentin", term_en="Augmentin", kind="drug")],
    )

    assert result.text == "Take Augmentin after food"
    assert result.confidence == 0.93
    prompt = client.messages.kwargs["messages"][0]["content"]
    assert "Augmentin" in prompt
    assert "Never add advice" in client.messages.kwargs["system"]


@pytest.mark.parametrize(
    "text",
    [
        "Take it. You should drink water.",
        '{"translation":"x","confidence":2}',
        '{"translation":"x","confidence":0.8,"extra":"no"}',
    ],
)
def test_claude_mt_rejects_malformed_output(text: str) -> None:
    with pytest.raises(ProviderOutputError):
        parse_mt_output(text)


def test_claude_reviewer_parses_entities() -> None:
    client = FakeAnthropicClient(
        '{"back_translation":"Uống 0.5 viên",'
        '"entities":[{"kind":"dose","source_text":"nửa viên","translated_text":"half a tablet"}],'
        '"flags":[]}'
    )
    provider = ClaudeReviewerProvider(api_key="", client=client)

    review = provider.review("Uống nửa viên", "Take half a tablet", "vi", "en")

    assert review.back_translation == "Uống 0.5 viên"
    assert review.entities[0].kind == "dose"
    assert review.entities[0].source_text == "nửa viên"
    assert review.entities[0].translated_text == "half a tablet"


@pytest.mark.parametrize(
    "text",
    [
        "{}",
        '{"back_translation":"","entities":[],"flags":[]}',
        '{"back_translation":"x","entities":[{"kind":"dose","source_span":[2],"translated_span":[0,1]}],"flags":[]}',
        '{"back_translation":"x","entities":[{"kind":"dose","source_text":2,"translated_text":"x"}],"flags":[]}',
    ],
)
def test_claude_reviewer_rejects_malformed_output(text: str) -> None:
    with pytest.raises(ProviderOutputError):
        parse_review_output(text)


@pytest.mark.live
def test_openai_asr_live_fixture_is_not_ci_default() -> None:
    pytest.skip("live golden-audio fixture runs only with real API keys and committed audio")
