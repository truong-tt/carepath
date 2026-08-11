import json
import urllib.error

import pytest

from app.config import Settings
from app.providers import get_providers
from app.providers.base import (
    ASRProvider,
    GlossaryEntry,
    MTProvider,
    ProviderOutputError,
    ReviewerProvider,
)
from app.providers.ckey import (
    CKeyChatClient,
    CKeyMTProvider,
    CKeyReviewerProvider,
    UnavailableASRProvider,
    can_retry_without_response_format,
    strip_json_fence,
)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self._body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class FakeOpener:
    """Records requests and replays queued responses or errors."""

    def __init__(self, *responses: object) -> None:
        self.queue = list(responses)
        self.requests: list[dict[str, object]] = []

    def __call__(self, request, timeout=None):
        self.requests.append(
            {
                "url": request.full_url,
                "headers": dict(request.headers),
                "body": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def http_error(code: int, body: str) -> urllib.error.HTTPError:
    import io

    return urllib.error.HTTPError(
        url="https://example.test/v1/chat/completions",
        code=code,
        msg="error",
        hdrs=None,
        fp=io.BytesIO(body.encode("utf-8")),
    )


def build_client(*responses: object, use_response_format: bool = False, attempts: int = 3):
    opener = FakeOpener(*responses)
    client = CKeyChatClient(
        api_key="sk-test",
        base_url="https://example.test/v1/",
        model="gpt-5.4",
        timeout=12,
        opener=opener,
        use_response_format=use_response_format,
        attempts=attempts,
        backoff_seconds=0,  # keep the suite fast
    )
    return client, opener


def test_suite_never_runs_against_a_real_gateway() -> None:
    """Fail loudly rather than quietly billing a real API from the test suite.

    Settings loads ../.env, so a developer with real credentials on disk would
    otherwise run the whole suite in cloud mode. conftest pins the environment;
    this asserts it took.
    """
    from app.config import get_settings

    settings = get_settings()
    assert settings.provider_mode == "mock", (
        f"tests must run in mock mode, got {settings.provider_mode!r}; "
        "a .env on disk is leaking into the suite"
    )
    assert not settings.llm_api_key


def test_registry_returns_ckey_contracts() -> None:
    providers = get_providers(Settings(provider_mode="ckey", llm_api_key="sk-test"))
    assert isinstance(providers.mt, MTProvider)
    assert isinstance(providers.reviewer, ReviewerProvider)
    assert isinstance(providers.asr, ASRProvider)


def test_missing_api_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        get_providers(Settings(provider_mode="ckey", llm_api_key=""))


def test_translate_posts_expected_request_shape() -> None:
    client, opener = build_client(
        FakeResponse(json.dumps({"translation": "I am allergic", "confidence": 0.9}))
    )
    result = CKeyMTProvider(client=client).translate(
        "Tôi bị dị ứng",
        "vi",
        "en",
        [GlossaryEntry(term_vi="dị ứng", term_en="allergy", kind="symptom", lasa_group=None)],
    )

    assert result.text == "I am allergic"
    assert result.confidence == 0.9

    sent = opener.requests[0]
    assert sent["url"] == "https://example.test/v1/chat/completions"
    assert sent["headers"]["Authorization"] == "Bearer sk-test"
    assert sent["timeout"] == 12
    body = sent["body"]
    assert body["model"] == "gpt-5.4"
    assert body["temperature"] == 0.0
    # Not sent by default: CKey's gpt-5.4 hangs on it. See CKeyChatClient.
    assert "response_format" not in body
    assert "medical interpreter" in body["messages"][0]["content"]
    payload = json.loads(body["messages"][1]["content"])
    assert payload["source_text"] == "Tôi bị dị ứng"
    assert payload["glossary"][0]["term_en"] == "allergy"


def test_translate_instructs_the_model_to_use_the_glossary() -> None:
    client, opener = build_client(
        FakeResponse(json.dumps({"translation": "ok", "confidence": 0.9}))
    )
    CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])
    assert "glossary" in opener.requests[0]["body"]["messages"][0]["content"].lower()


def test_translate_accepts_fenced_json() -> None:
    client, _ = build_client(
        FakeResponse('```json\n{"translation": "hello", "confidence": 0.8}\n```')
    )
    assert CKeyMTProvider(client=client).translate("xin chào", "vi", "en", []).text == "hello"


@pytest.mark.parametrize(
    "content",
    [
        '{"translation": "hi"}',
        '{"translation": "", "confidence": 0.9}',
        '{"translation": "hi", "confidence": 0.9, "note": "extra"}',
        "not json at all",
    ],
)
def test_malformed_translation_output_is_rejected(content: str) -> None:
    client, _ = build_client(FakeResponse(content))
    with pytest.raises(ProviderOutputError):
        CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])


@pytest.mark.parametrize("bad", ["4", "95", "-1", '"high"', "null"])
def test_an_unusable_confidence_degrades_instead_of_dropping_the_turn(bad: str) -> None:
    """A model answering 95 for 95% must not cost the clinician a translation.

    Confidence has a safe default and the translation does not, so the turn
    survives at zero confidence and takes the low-confidence path.
    """
    client, _ = build_client(FakeResponse(f'{{"translation": "hello", "confidence": {bad}}}'))

    result = CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])

    assert result.text == "hello"
    assert result.confidence == 0.0


def test_retries_without_response_format_when_gateway_rejects_it() -> None:
    client, opener = build_client(
        http_error(400, "response_format is not supported"),
        FakeResponse(json.dumps({"translation": "hello", "confidence": 0.9})),
        use_response_format=True,
    )
    assert CKeyMTProvider(client=client).translate("xin chào", "vi", "en", []).text == "hello"
    assert "response_format" in opener.requests[0]["body"]
    assert "response_format" not in opener.requests[1]["body"]


def test_response_format_is_opt_in() -> None:
    """A hang is not an HTTPError, so the retry above cannot rescue a timeout.

    CKey's gpt-5.4 hangs when sent response_format, which is why the default is
    off rather than on-with-a-retry.
    """
    client, opener = build_client(
        FakeResponse(json.dumps({"translation": "hi", "confidence": 0.9})),
        use_response_format=True,
    )
    CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])
    assert opener.requests[0]["body"]["response_format"] == {"type": "json_object"}


def test_client_errors_fail_immediately_without_leaking_the_body() -> None:
    client, opener = build_client(http_error(401, "Tôi bị dị ứng amoxicillin"))
    with pytest.raises(RuntimeError) as excinfo:
        CKeyMTProvider(client=client).translate("Tôi bị dị ứng amoxicillin", "vi", "en", [])
    assert "dị ứng" not in str(excinfo.value)
    assert "401" in str(excinfo.value)
    assert len(opener.requests) == 1, "a client error will not fix itself"


def test_retries_a_transient_gateway_error() -> None:
    """Measured: this gateway intermittently 502s. One blip must not drop a turn."""
    client, opener = build_client(
        http_error(502, "Bad Gateway"),
        FakeResponse(json.dumps({"translation": "hello", "confidence": 0.9})),
    )
    assert CKeyMTProvider(client=client).translate("xin chào", "vi", "en", []).text == "hello"
    assert len(opener.requests) == 2


def test_retries_a_timeout() -> None:
    client, opener = build_client(
        TimeoutError("read timed out"),
        FakeResponse(json.dumps({"translation": "hello", "confidence": 0.9})),
    )
    assert CKeyMTProvider(client=client).translate("xin chào", "vi", "en", []).text == "hello"
    assert len(opener.requests) == 2


def test_gives_up_after_the_attempt_budget() -> None:
    client, opener = build_client(
        http_error(502, "Bad Gateway"),
        http_error(502, "Bad Gateway"),
        http_error(503, "Service Unavailable"),
        attempts=3,
    )
    with pytest.raises(RuntimeError, match="after 3 attempts"):
        CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])
    assert len(opener.requests) == 3


def test_unexpected_response_shape_is_rejected() -> None:
    class BadResponse(FakeResponse):
        def __init__(self) -> None:
            self._body = json.dumps({"unexpected": True}).encode("utf-8")

    client, _ = build_client(BadResponse())
    with pytest.raises(RuntimeError):
        CKeyMTProvider(client=client).translate("xin chào", "vi", "en", [])


def test_reviewer_parses_entities() -> None:
    payload = {
        "back_translation": "I am allergic to amoxicillin",
        "entities": [
            {"kind": "allergen", "source_text": "amoxicillin", "translated_text": "amoxicillin"}
        ],
        "flags": [],
    }
    client, opener = build_client(FakeResponse(json.dumps(payload)))
    review = CKeyReviewerProvider(client=client).review(
        "Tôi bị dị ứng amoxicillin", "I am allergic to amoxicillin", "vi", "en"
    )
    assert review.entities[0].source_text == "amoxicillin"
    sent = json.loads(opener.requests[0]["body"]["messages"][1]["content"])
    assert sent["translation"] == "I am allergic to amoxicillin"


def test_audio_turns_fail_closed_in_ckey_mode() -> None:
    with pytest.raises(RuntimeError, match="text_turn"):
        UnavailableASRProvider().transcribe(b"audio", "en")


def test_strip_json_fence_leaves_bare_json_alone() -> None:
    assert strip_json_fence('{"a": 1}') == '{"a": 1}'
    assert strip_json_fence('```json\n{"a": 1}\n```') == '{"a": 1}'


@pytest.mark.parametrize(
    ("code", "body", "expected"),
    [
        (400, "response_format unsupported", True),
        (422, "json_object invalid", True),
        (400, "bad model", False),
        (500, "response_format", False),
    ],
)
def test_response_format_retry_predicate(code: int, body: str, expected: bool) -> None:
    assert can_retry_without_response_format(code, body) is expected
