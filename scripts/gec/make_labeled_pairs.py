"""CLI: build supplementary real GEC pairs from the Label Studio export.

    python scripts/gec/make_labeled_pairs.py \
      --input data/labeling/training_transcripts.jsonl \
      --output artifacts/gec_pairs/vimedcss_labeled_pairs.jsonl \
      --datastore artifacts/retrieval/term_datastore.json --resume

The export already carries real ``raw_asr`` (Whisper draft) + clinician-edited
``gold_text``, so each kept row is a real hypothesis->gold pair. These are merged
into training as supplementary real data (ViMedCSS stays primary). Pass
``--audio-root DIR --n-best 5`` to add perturbation N-best when the audio is local.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.config import Settings  # noqa: E402
from carepath.gec.data import build_labeled_pairs, read_jsonl  # noqa: E402
from carepath.gec.retrieval import build_ne_retriever  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/labeling/training_transcripts.jsonl")
    parser.add_argument("--output", default="artifacts/gec_pairs/vimedcss_labeled_pairs.jsonl")
    parser.add_argument("--datastore", default="data/medical_lexicon.json")
    parser.add_argument(
        "--retrieval-backend", default="lexical", choices=["lexical", "semantic", "hybrid"]
    )
    parser.add_argument("--audio-root", default=None, help="local dir holding audio_file clips")
    parser.add_argument("--n-best", type=int, default=1, help=">1 needs --audio-root + audio")
    parser.add_argument("--split", default="train")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env()
    retriever = build_ne_retriever(
        Path(args.datastore), backend=args.retrieval_backend, top_k=settings.retrieval_top_k
    )

    asr = None
    if args.audio_root and args.n_best > 1:
        from carepath.services.asr import build_asr_service

        asr = build_asr_service(settings)

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(
            f"No labeling export at {input_path}. Run the labeling workflow first "
            "(docs/vietnamese_labeling_guide.md)."
        )
    rows = read_jsonl(input_path)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _completed(output_path) if args.resume else set()
    mode = "a" if args.resume and output_path.exists() else "w"

    written = 0
    with output_path.open(mode, encoding="utf-8") as handle:
        for pair in build_labeled_pairs(
            rows,
            retriever,
            audio_root=Path(args.audio_root) if args.audio_root else None,
            asr=asr,
            n_best=args.n_best,
            split=args.split,
            completed_ids=completed,
        ):
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1
    print(f"Wrote {written} labeled GEC pairs to {output_path}")


def _completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line).get("audio_id"))
    return ids


if __name__ == "__main__":
    main()
