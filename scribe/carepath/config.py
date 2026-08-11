from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from carepath.services.tts import DEFAULT_TTS_REPO


def load_env_file(path: Path = Path(".env")) -> None:
    """Load simple KEY=VALUE entries without overriding real environment vars."""

    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _csv_env(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(
        value
        for value in (item.strip().rstrip("/") for item in raw.split(","))
        if value
    )


@dataclass(frozen=True)
class Settings:
    app_env: str
    asr_provider: str
    allow_mock_asr: bool
    gipformer_quantize: str
    gipformer_num_threads: int
    gipformer_decoding_method: str
    gipformer_chunk_seconds: float
    gipformer_segmentation: str
    gipformer_overlap_seconds: float
    gipformer_max_segment_seconds: float
    gipformer_vad_model: str | None
    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_api_key: str | None
    llm_timeout_seconds: float
    medical_lexicon_path: Path
    retrieval_top_k: int
    retrieval_backend: str
    semantic_model_name: str
    # onnxruntime execution provider for Gipformer ("cpu" or "cuda"). With "cuda",
    # onnxruntime falls back to CPU (with a warning) when no GPU EP is available,
    # so it is always safe to request.
    gipformer_provider: str = "cpu"
    llm_fallback_offline: bool = True
    # Off by default: measured 2026-08-11, CKey's gpt-5.4 hangs past a 60s
    # timeout when sent response_format=json_object but answers in ~8s without
    # it. The prompts demand strict JSON and the parsers validate it, so the
    # flag buys nothing here. Turn it on for a gateway that needs the hint.
    llm_json_response_format: bool = False
    # Server-side Vietnamese speech. A default Windows or macOS install has no
    # vi-VN voice, so the browser cannot speak the clinician's language.
    tts_provider: str = "piper"
    tts_repo_id: str = DEFAULT_TTS_REPO
    # Deliberately short and repo-relative: espeak-ng reads its data with a
    # native call that fails past the Windows MAX_PATH limit, and the HF cache
    # path is already ~250 characters.
    tts_model_dir: Path = Path("models/vi-tts")
    cors_origins: tuple[str, ...] = ()
    team_code: str | None = None
    soap_rate_limit_per_ip_hour: int = 3
    soap_rate_limit_per_ip_day: int = 10
    soap_rate_limit_global_day: int = 100
    # gec_local provider: serve a trained QLoRA adapter bundle in-process.
    gec_bundle_path: str | None = None
    gec_soap_delegate: str = "offline"
    # scribe_local provider: private research staging bundle with GEC + SOAP
    # adapters sharing one base model. Never selected by production defaults.
    scribe_bundle_path: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        llm_provider = os.getenv("LLM_PROVIDER", "offline").strip().lower()
        default_llm_base_url = (
            "https://api.xah.io/v1"
            if llm_provider == "ckey"
            else "https://api.openai.com/v1"
        )
        default_llm_model = "gpt-5.4" if llm_provider == "ckey" else "gpt-4.1-mini"
        chunk_seconds = _float_env("GIPFORMER_CHUNK_SECONDS", 20.0)
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            asr_provider=os.getenv("ASR_PROVIDER", "gipformer").strip().lower(),
            allow_mock_asr=_bool_env("ALLOW_MOCK_ASR", False),
            gipformer_quantize=os.getenv("GIPFORMER_QUANTIZE", "int8").strip().lower(),
            gipformer_num_threads=_int_env("GIPFORMER_NUM_THREADS", os.cpu_count() or 4),
            gipformer_provider=os.getenv("GIPFORMER_PROVIDER", "cpu").strip().lower(),
            gipformer_decoding_method=os.getenv(
                "GIPFORMER_DECODING_METHOD", "modified_beam_search"
            ).strip(),
            gipformer_chunk_seconds=chunk_seconds,
            gipformer_segmentation=os.getenv(
                "GIPFORMER_SEGMENTATION", "overlap"
            ).strip().lower(),
            gipformer_overlap_seconds=_float_env("GIPFORMER_OVERLAP_SECONDS", 2.0),
            gipformer_max_segment_seconds=_float_env(
                "GIPFORMER_MAX_SEGMENT_SECONDS", chunk_seconds
            ),
            gipformer_vad_model=os.getenv("GIPFORMER_VAD_MODEL") or None,
            llm_provider=llm_provider,
            llm_base_url=os.getenv("LLM_BASE_URL", default_llm_base_url).rstrip("/"),
            llm_model=os.getenv("LLM_MODEL", default_llm_model).strip(),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_timeout_seconds=_float_env("LLM_TIMEOUT_SECONDS", 60.0),
            medical_lexicon_path=Path(
                os.getenv("MEDICAL_LEXICON_PATH", "data/medical_lexicon.json")
            ),
            retrieval_top_k=_int_env("RETRIEVAL_TOP_K", 5),
            retrieval_backend=os.getenv("RETRIEVAL_BACKEND", "lexical").strip().lower(),
            semantic_model_name=os.getenv(
                "SEMANTIC_MODEL_NAME", "bkai-foundation-models/vietnamese-bi-encoder"
            ).strip(),
            llm_fallback_offline=_bool_env("LLM_FALLBACK_OFFLINE", True),
            llm_json_response_format=_bool_env("LLM_JSON_RESPONSE_FORMAT", False),
            tts_provider=os.getenv("TTS_PROVIDER", "piper").strip().lower(),
            tts_repo_id=os.getenv("TTS_REPO_ID", DEFAULT_TTS_REPO).strip(),
            tts_model_dir=Path(os.getenv("TTS_MODEL_DIR", "models/vi-tts")),
            cors_origins=_csv_env("CORS_ORIGINS"),
            team_code=os.getenv("TEAM_CODE") or None,
            soap_rate_limit_per_ip_hour=_int_env("SOAP_RATE_LIMIT_PER_IP_HOUR", 3),
            soap_rate_limit_per_ip_day=_int_env("SOAP_RATE_LIMIT_PER_IP_DAY", 10),
            soap_rate_limit_global_day=_int_env("SOAP_RATE_LIMIT_GLOBAL_DAY", 100),
            gec_bundle_path=os.getenv("GEC_BUNDLE_PATH") or None,
            gec_soap_delegate=os.getenv("GEC_SOAP_DELEGATE", "offline").strip().lower(),
            scribe_bundle_path=os.getenv("SCRIBE_BUNDLE_PATH") or None,
        )


def load_settings() -> Settings:
    load_env_file(Path(os.getenv("CAREPATH_ENV_FILE", ".env")))
    return Settings.from_env()
