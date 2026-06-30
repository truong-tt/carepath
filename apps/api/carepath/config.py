from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
    llm_fallback_offline: bool = True
    # gec_local provider: serve a trained QLoRA adapter bundle in-process.
    gec_bundle_path: str | None = None
    gec_soap_delegate: str = "offline"

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
            gipformer_num_threads=_int_env("GIPFORMER_NUM_THREADS", 4),
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
            gec_bundle_path=os.getenv("GEC_BUNDLE_PATH") or None,
            gec_soap_delegate=os.getenv("GEC_SOAP_DELEGATE", "offline").strip().lower(),
        )


def load_settings() -> Settings:
    load_env_file(Path(os.getenv("CAREPATH_ENV_FILE", ".env")))
    return Settings.from_env()
