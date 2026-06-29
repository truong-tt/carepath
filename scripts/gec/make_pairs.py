"""CLI: build real GEC pairs by running Gipformer over ViMedCSS audio (paper §3.1).

    python scripts/gec/make_pairs.py \
      --output artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
      --limit-per-split 20 --datastore artifacts/retrieval/term_datastore_smoke.json --resume

Use --asr-provider mock for a dependency-light smoke run.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.config import Settings  # noqa: E402
from carepath.gec.data import build_real_pairs  # noqa: E402
from carepath.gec.retrieval import build_ne_retriever  # noqa: E402
from carepath.services.asr import build_asr_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--output", default="artifacts/gec_pairs/vimedcss_gipformer_pairs.jsonl")
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test", "hard"])
    parser.add_argument("--limit-per-split", type=int, default=None)
    parser.add_argument("--asr-provider", default="gipformer", choices=["gipformer", "mock"])
    parser.add_argument("--datastore", default="data/medical_lexicon.json")
    parser.add_argument("--retrieval-backend", default="lexical", choices=["lexical", "semantic", "hybrid"])
    parser.add_argument("--n-best", type=int, default=1, help="paper N=5; >1 adds perturbation N-best")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    settings = Settings.from_env()
    if args.asr_provider == "mock":
        settings = replace(settings, asr_provider="mock", allow_mock_asr=True)
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
        for pair in build_real_pairs(
            dataset=args.dataset,
            splits=args.splits,
            retriever=retriever,
            asr=asr,
            limit_per_split=args.limit_per_split,
            completed_ids=completed,
            n_best=args.n_best,
        ):
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
            handle.flush()
            written += 1
    print(f"Wrote {written} real GEC pairs to {output_path}")


def _completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            ids.add(f"{row.get('split')}:{row.get('audio_id')}")
    return ids


if __name__ == "__main__":
    main()
