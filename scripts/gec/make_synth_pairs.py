"""CLI: build synthetic GEC pairs by running Gipformer over TTS audio (paper §4.1 Step 3).

    python scripts/gec/make_synth_pairs.py \
      --input artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
      --output artifacts/gec_pairs/darag_synthetic_pairs_smoke.jsonl \
      --datastore artifacts/retrieval/term_datastore_smoke.json --limit 10 --resume
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
from carepath.gec.data import build_synthetic_pairs, read_jsonl, validate_gec_pair  # noqa: E402
from carepath.gec.retrieval import build_ne_retriever  # noqa: E402
from carepath.services.asr import build_asr_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL from voice_clone_tts.py")
    parser.add_argument("--output", default="artifacts/gec_pairs/darag_synthetic_pairs.jsonl")
    parser.add_argument("--datastore", default="data/medical_lexicon.json")
    parser.add_argument("--retrieval-backend", default="lexical", choices=["lexical", "semantic", "hybrid"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    if args.limit:
        rows = rows[: args.limit]

    settings = Settings.from_env()
    asr = build_asr_service(settings)
    retriever = build_ne_retriever(
        Path(args.datastore), backend=args.retrieval_backend, top_k=settings.retrieval_top_k
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _completed(output_path) if args.resume else set()
    mode = "a" if args.resume and output_path.exists() else "w"

    written = 0
    with output_path.open(mode, encoding="utf-8") as handle:
        for pair in build_synthetic_pairs(rows, retriever=retriever, asr=asr, completed_ids=completed):
            result = validate_gec_pair(pair)
            if not result.ok:
                raise ValueError(f"Invalid synthetic pair {pair.get('audio_id')}: {result.errors}")
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1
    print(f"Wrote {written} synthetic GEC pairs to {output_path}")


def _completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row["audio_id"] for row in read_jsonl(path) if row.get("audio_id")}


if __name__ == "__main__":
    main()
