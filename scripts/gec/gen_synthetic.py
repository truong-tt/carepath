"""CLI: generate synthetic in-domain transcripts (paper §4.1 Step 1).

    # inspect the few-shot prompt without loading a model:
    python scripts/gec/gen_synthetic.py --dry-run \
      --pairs artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl

    # real generation (GPU):
    python scripts/gec/gen_synthetic.py \
      --pairs artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
      --output artifacts/synthetic/synthetic_clean_smoke.jsonl --count 50 --load-in-4bit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.config import DEFAULT_SYNTH_MODEL, FALLBACK_SYNTH_MODELS  # noqa: E402
from carepath.gec.data import read_jsonl  # noqa: E402
from carepath.gec.prompts import build_synthetic_generation_messages  # noqa: E402
from carepath.gec.synthetic import (  # noqa: E402
    generate_synthetic_transcripts,
    load_examples,
    load_generator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/synthetic/synthetic_clean.jsonl")
    parser.add_argument("--pairs", default=None, help="GEC pair JSONL for few-shot examples.")
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    parser.add_argument("--split", default="train")
    parser.add_argument("--model", default=DEFAULT_SYNTH_MODEL)
    parser.add_argument("--fallback-models", nargs="+", default=list(FALLBACK_SYNTH_MODELS))
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--examples-per-prompt", type=int, default=4)
    parser.add_argument("--limit-source", type=int, default=200)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    examples = load_examples(
        Path(args.pairs) if args.pairs else None, args.dataset, args.split, args.limit_source
    )
    if not examples:
        raise SystemExit("No examples found for synthetic generation.")

    if args.dry_run:
        messages = build_synthetic_generation_messages(
            examples[: args.examples_per_prompt], count=min(args.batch_size, args.count)
        )
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return

    output_path = Path(args.output)
    existing = [r["clean_text"] for r in read_jsonl(output_path) if r.get("clean_text")]
    model_label, generator = load_generator(
        [args.model, *args.fallback_models], load_in_4bit=args.load_in_4bit
    )

    rows = generate_synthetic_transcripts(
        examples=examples,
        count=max(0, args.count - len(existing)),
        generate_fn=generator,
        existing_texts=existing,
        examples_per_prompt=args.examples_per_prompt,
        batch_size=args.batch_size,
        model_label=model_label,
        seed=args.seed,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} new synthetic transcripts to {output_path}")


if __name__ == "__main__":
    main()
