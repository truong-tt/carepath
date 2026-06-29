"""CLI: voice-cloning TTS over synthetic transcripts (paper §4.1 Step 2 / App. D).

Conditions the TTS model on random in-domain ViMedCSS reference clips so the
synthetic speech mimics real speakers (the paper's voice cloning).

    python scripts/gec/voice_clone_tts.py \
      --input artifacts/synthetic/synthetic_clean_smoke.jsonl \
      --output artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
      --provider xtts --ref-dataset tensorxt/ViMedCSS --ref-count 20 --limit 10 --resume

Use --provider mms for the single-speaker (no-clone) labeled fallback.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.data import read_jsonl  # noqa: E402
from carepath.gec.tts import (  # noqa: E402
    ReferenceClipSampler,
    build_synthesizer,
    load_completed_audio_ids,
    synthesize_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL from gen_synthetic.py")
    parser.add_argument("--output", default="artifacts/synthetic/synthetic_audio_manifest.jsonl")
    parser.add_argument("--audio-dir", default="artifacts/synthetic/audio")
    parser.add_argument("--provider", default="xtts", choices=["xtts", "mms"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--language", default="vi")
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("--ref-dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--ref-split", default="train")
    parser.add_argument("--ref-count", type=int, default=20)
    parser.add_argument("--ref-dir", default=None, help="Use local wavs instead of a dataset.")
    parser.add_argument("--ref-cache", default="artifacts/synthetic/reference_clips")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    sampler = None
    if args.provider == "xtts":
        if args.ref_dir:
            sampler = ReferenceClipSampler.from_directory(Path(args.ref_dir))
        else:
            sampler = ReferenceClipSampler.from_dataset(
                args.ref_dataset, args.ref_split, args.ref_count, Path(args.ref_cache)
            )

    synthesizer = build_synthesizer(
        provider=args.provider, model=args.model, language=args.language, use_gpu=not args.no_gpu
    )
    output_path = Path(args.output)
    completed = load_completed_audio_ids(output_path) if args.resume else set()
    written = synthesize_manifest(
        clean_rows=rows,
        synthesizer=synthesizer,
        audio_dir=Path(args.audio_dir),
        sampler=sampler,
        output_path=output_path,
        completed_ids=completed,
    )
    print(f"Wrote {written} synthetic audio rows (provider={synthesizer.provider}) to {output_path}")


if __name__ == "__main__":
    main()
