"""Single source of truth for every pipeline artifact path.

Both notebooks used to repeat string literals like
``artifacts/gec_pairs/vimedcss_gipformer_pairs.jsonl`` — easy to mistype and easy
to drift between the two files. ``ArtifactPaths`` derives every path from one root
and one ``suffix`` (``"_smoke"`` for smoke runs), so a stage notebook just reads
``paths.real_pairs``. Adapters can point at a Drive-backed ``adapters_root`` so an
interrupted Colab run resumes from checkpoints on Drive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path = Path("artifacts")
    suffix: str = ""                       # "_smoke" for smoke runs
    adapters_root: Path | None = None      # Drive override; else <root>/gec_lora/qwen3

    def _name(self, stem: str, ext: str) -> str:
        return f"{stem}{self.suffix}.{ext}"

    # --- datastore / pairs -------------------------------------------------
    @property
    def datastore(self) -> Path:
        return self.root / "retrieval" / self._name("term_datastore", "json")

    @property
    def real_pairs(self) -> Path:
        return self.root / "gec_pairs" / self._name("vimedcss_gipformer_pairs", "jsonl")

    @property
    def synth_clean(self) -> Path:
        return self.root / "synthetic" / self._name("synthetic_clean", "jsonl")

    @property
    def tts_manifest(self) -> Path:
        return self.root / "synthetic" / self._name("synthetic_audio_manifest", "jsonl")

    @property
    def synth_pairs(self) -> Path:
        return self.root / "gec_pairs" / self._name("darag_synthetic_pairs", "jsonl")

    @property
    def augmented(self) -> Path:
        return self.root / "gec_pairs" / self._name("darag_augmented", "jsonl")

    # --- evaluations -------------------------------------------------------
    @property
    def evaluations(self) -> Path:
        return self.root / "evaluations"

    @property
    def leakage(self) -> Path:
        return self.evaluations / self._name("leakage", "json")

    @property
    def raw_baseline_wer(self) -> Path:
        return self.evaluations / self._name("raw_baseline_wer", "json")

    @property
    def llm_rag(self) -> Path:
        return self.evaluations / self._name("llm_rag", "jsonl")

    @property
    def darag_preds(self) -> Path:
        return self.evaluations / self._name("darag_all_preds", "jsonl")

    @property
    def darag_wer(self) -> Path:
        return self.evaluations / self._name("darag_wer", "json")

    @property
    def darag_ne_f1(self) -> Path:
        return self.evaluations / self._name("darag_ne_f1", "json")

    @property
    def darag_stratified(self) -> Path:
        return self.evaluations / self._name("darag_stratified", "json")

    @property
    def frozen_preds(self) -> Path:
        return self.evaluations / self._name("frozen_eval_preds", "jsonl")

    @property
    def frozen_wer(self) -> Path:
        return self.evaluations / self._name("frozen_eval_wer", "json")

    @property
    def frozen_ne_f1(self) -> Path:
        return self.evaluations / self._name("frozen_eval_ne_f1", "json")

    @property
    def frozen_stratified(self) -> Path:
        return self.evaluations / self._name("frozen_eval_stratified", "json")

    # --- adapters / sharing ------------------------------------------------
    @property
    def adapters(self) -> Path:
        return self.adapters_root or (self.root / "gec_lora" / "qwen3")

    @property
    def share(self) -> Path:
        return self.root / "share"

    @property
    def serve_bundle(self) -> Path:
        """Self-describing deploy bundle (manifest + adapter + datastore)."""
        return self.root / f"gec_serve{self.suffix}"

    def restore_set(self) -> list[str]:
        """Artifacts a GPU stage restores from Drive before it can run."""
        return [str(self.datastore), str(self.real_pairs)]
