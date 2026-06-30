"""Serve a trained DARAG GEC adapter in-process (LLM_PROVIDER=gec_local).

Loads the QLoRA adapter bundled by ``scripts/gec/export_serve.py`` and corrects
transcripts with it, using the retrieved NEs the serving retriever already
produces (RAC at inference, paper §4.2). The bundle's ``serve_manifest.json``
carries the frozen DARAG prompt, so this serving module does **not** import
``carepath.gec.*`` — research and serving stay decoupled.

Design choices for a clinical MVP:
* heavy ML deps (torch/peft/transformers) import lazily on first use, like the
  offline pipeline, so importing this module never needs a GPU stack;
* a **safety gate** rejects empty / runaway output and raises ``LLMError`` so the
  existing ``FallbackClinicalLLM`` transparently serves the offline corrector —
  a bad adapter never blocks the demo;
* SOAP drafting is delegated to a configured clinical LLM — the 4B correction
  adapter is not a SOAP model.

GPU note: Qwen3-4B in 4-bit needs CUDA to be usable at request latency. On a
CPU-only box prefer the network LLM provider, or stand up a GEC microservice.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

from carepath.config import Settings
from carepath.services.llm import (
    ClinicalLLM,
    CorrectionResult,
    LLMError,
    OfflineClinicalLLM,
    OpenAICompatibleLLM,
    SoapResult,
)
from carepath.services.retrieval import RetrievedTerm

logger = logging.getLogger("carepath.gec_local")


class LocalGecLLM:
    """ClinicalLLM backed by a local QLoRA GEC adapter bundle."""

    def __init__(
        self,
        bundle_path: Path,
        soap_delegate: ClinicalLLM,
        generate_fn: Callable[[str], str] | None = None,
        max_new_tokens: int | None = None,
    ):
        self.bundle = Path(bundle_path)
        self.manifest = json.loads((self.bundle / "serve_manifest.json").read_text("utf-8"))
        self.soap_delegate = soap_delegate
        self.max_new_tokens = max_new_tokens or int(self.manifest.get("max_new_tokens", 256))
        self._generate_fn = generate_fn  # injectable for tests (skips model load)
        self._model = None
        self._tokenizer = None

    # -- readiness ---------------------------------------------------------
    def readiness(self) -> tuple[bool, dict[str, object]]:
        adapter = self.bundle / self.manifest.get("adapter_dir", "adapter")
        ready = adapter.exists()
        return ready, {
            "provider": "gec_local",
            "bundle": str(self.bundle),
            "base_model": self.manifest.get("base_model"),
            "variant": self.manifest.get("variant"),
            "missing_adapter": not ready,
            "fallback": "offline",
        }

    # -- correction --------------------------------------------------------
    def correct_transcript(
        self,
        raw_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> CorrectionResult:
        prompt = self._build_prompt(raw_text, retrieved_terms)
        try:
            raw_out = self._generate(prompt)
        except LLMError:
            raise
        except Exception as exc:  # model/CUDA failure → degrade via fallback
            raise LLMError(f"gec_local generation failed: {exc}") from exc
        corrected = _strip(raw_out, self.manifest["prompt"]["im_end"])
        if not _passes_safety(raw_text, corrected):
            raise LLMError("gec_local output failed safety gate")
        return CorrectionResult(corrected_text=corrected, provider="gec_local", raw_response=raw_out)

    def generate_soap(
        self,
        corrected_text: str,
        retrieved_terms: list[RetrievedTerm],
        encounter_context: str | None = None,
    ) -> SoapResult:
        # The correction adapter is not a SOAP model; delegate.
        return self.soap_delegate.generate_soap(
            corrected_text, retrieved_terms, encounter_context=encounter_context
        )

    # -- internals ---------------------------------------------------------
    def _build_prompt(self, raw_text: str, retrieved_terms: list[RetrievedTerm]) -> str:
        p = self.manifest["prompt"]
        lines = [f"{p['best_label']}{raw_text}"]
        # Serving has a single Gipformer decode, so no N-best 'other hypotheses'.
        if self.manifest.get("use_retrieval", True) and retrieved_terms:
            names = ", ".join(t.term for t in retrieved_terms)
            lines.append(f"{p['entities_label']}{names}")
        user = "\n".join(lines)
        return (
            f"{p['im_start']}system\n{p['system']}\n{p['im_end']}\n"
            f"{p['im_start']}user\n{user}\n{p['im_end']}\n"
            f"{p['im_start']}assistant\n"
        )

    def _generate(self, prompt: str) -> str:
        if self._generate_fn is not None:
            return self._generate_fn(prompt)
        self._ensure_model()
        import torch  # type: ignore

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        with torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                num_beams=1,
                pad_token_id=self._tokenizer.pad_token_id,
            )
        generated = output[0][inputs["input_ids"].shape[-1] :]
        return self._tokenizer.decode(generated, skip_special_tokens=True)

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        import torch  # type: ignore
        from peft import PeftModel  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        adapter_dir = self.bundle / self.manifest.get("adapter_dir", "adapter")
        base_model = self.manifest["base_model"]
        tokenizer_src = str(adapter_dir) if (adapter_dir / "tokenizer_config.json").exists() else base_model
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_src, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        base = AutoModelForCausalLM.from_pretrained(
            base_model, quantization_config=bnb, device_map="auto", trust_remote_code=True
        )
        model = PeftModel.from_pretrained(base, str(adapter_dir))
        model.eval()
        self._model, self._tokenizer = model, tokenizer
        logger.info("Loaded gec_local adapter from %s on %s", adapter_dir, base.device)


def _strip(text: str, im_end: str) -> str:
    return text.split(im_end)[0].strip()


def _passes_safety(raw_text: str, corrected: str) -> bool:
    """Clinical guard: reject empty or runaway corrections (length sanity)."""

    if not corrected.strip():
        return False
    raw_words = max(1, len(raw_text.split()))
    ratio = len(corrected.split()) / raw_words
    return 0.5 <= ratio <= 2.0


def build_gec_local(settings: Settings) -> ClinicalLLM:
    """Construct a LocalGecLLM with a SOAP delegate from settings."""

    if not settings.gec_bundle_path:
        raise ValueError("GEC_BUNDLE_PATH is required for the gec_local provider")
    if settings.gec_soap_delegate == "offline":
        soap: ClinicalLLM = OfflineClinicalLLM()
    else:
        soap = OpenAICompatibleLLM(settings)
    return LocalGecLLM(Path(settings.gec_bundle_path), soap_delegate=soap)
