"""CLI: run the DARAG pipeline end-to-end (or a single stage) for a profile.

    # plumbing check (mock ASR, tiny limits, no models needed):
    python scripts/gec/run_pipeline.py --profile smoke --stage data

    # real ViMedCSS run on a GPU box:
    python scripts/gec/run_pipeline.py --profile full --stage all

Stages: ``data`` (datastore + real pairs + labeled pairs), ``synth`` (synthetic
transcripts + TTS + synthetic pairs + leakage), ``train`` (augment + QLoRA), and
``eval`` (LLM/RAG baseline + predict + tables + gate). Each stage is independently
runnable and resumable; ``all`` runs them in order. Paths and run-sizes come from
``carepath.gec.paths`` / ``carepath.gec.profiles`` so this mirrors the notebooks.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from carepath.gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from carepath.gec.data import read_jsonl  # noqa: E402
from carepath.gec.paths import ArtifactPaths  # noqa: E402
from carepath.gec.profiles import get_profile  # noqa: E402

STAGES = ("all", "data", "synth", "train", "eval")
LEXICON = "data/medical_lexicon.json"
LABELING_EXPORT = "data/labeling/training_transcripts.jsonl"


def run(args: list) -> None:
    run_env = dict(os.environ)
    run_env["PYTHONPATH"] = "apps/api"
    run_env["PYTHONIOENCODING"] = "utf-8"
    printable = " ".join(str(a) for a in args)
    print("\n>>>", printable, flush=True)
    proc = subprocess.run([sys.executable, *map(str, args)], env=run_env)
    if proc.returncode != 0:
        raise SystemExit(f"step failed ({proc.returncode}): {printable}")


def stage_data(p: ArtifactPaths, prof, dataset: str) -> None:
    limit = str(prof.limit_per_split or 0)
    run(["scripts/gec/build_datastore.py", "--dataset", dataset,
         "--limit-per-split", limit, "--output", str(p.datastore)])
    run(["scripts/gec/make_pairs.py", "--dataset", dataset, "--output", str(p.real_pairs),
         "--asr-provider", prof.asr_provider, "--datastore", str(p.datastore),
         "--retrieval-backend", prof.retrieval_backend, "--limit-per-split", limit,
         "--n-best", str(prof.n_best), "--resume"])
    if Path(LABELING_EXPORT).exists():
        run(["scripts/gec/make_labeled_pairs.py", "--input", LABELING_EXPORT,
             "--output", str(p.labeled_pairs), "--datastore", str(p.datastore),
             "--retrieval-backend", prof.retrieval_backend, "--resume"])
    else:
        print(f"(no {LABELING_EXPORT} — skipping supplementary labeled pairs)")


def stage_synth(p: ArtifactPaths, prof) -> None:
    count = prof.synth_count
    if count is None:  # paper nsyn = n: match the real train size
        count = sum(1 for r in read_jsonl(p.real_pairs) if r.get("split") == "train") or 50
    gen = ["scripts/gec/gen_synthetic.py", "--pairs", str(p.real_pairs),
           "--output", str(p.synth_clean), "--count", str(count)]
    if prof.name != "smoke":
        gen.append("--load-in-4bit")
    run(gen)
    tts = ["scripts/gec/voice_clone_tts.py", "--input", str(p.synth_clean),
           "--output", str(p.tts_manifest), "--provider", prof.tts_provider,
           "--ref-dataset", "tensorxt/ViMedCSS", "--ref-count", "20", "--resume"]
    if prof.synth_tts_limit:
        tts += ["--limit", str(prof.synth_tts_limit)]
    run(tts)
    run(["scripts/gec/make_synth_pairs.py", "--input", str(p.tts_manifest),
         "--output", str(p.synth_pairs), "--datastore", str(p.datastore),
         "--n-best", str(prof.n_best), "--resume"])
    run(["scripts/gec/check_leakage.py", "--synthetic", str(p.synth_clean),
         "--real", str(p.real_pairs), "--output", str(p.leakage)])


def stage_train(p: ArtifactPaths, prof) -> None:
    real_inputs = [str(p.real_pairs)]
    if p.labeled_pairs.exists():
        real_inputs.append(str(p.labeled_pairs))
    # Learn real ASR confusions (paper Limitation #1) into the datastore, then
    # refresh every pair's retrieved NEs so the RAC prompt carries the right term.
    harvest_pairs = list(real_inputs)
    if p.synth_pairs.exists():
        harvest_pairs.append(str(p.synth_pairs))
    run(["scripts/gec/harvest_aliases.py", "--datastore", str(p.datastore),
         "--pairs", *harvest_pairs, "--refresh", "--backend", prof.retrieval_backend])
    run(["scripts/gec/augment.py", "--real", *real_inputs, "--synthetic", str(p.synth_pairs),
         "--output", str(p.augmented), "--nsyn-factor", str(prof.nsyn_factor)])
    train = ["scripts/gec/train.py", "--pairs", str(p.augmented), "--output-dir", str(p.adapters),
             "--max-steps", str(prof.max_steps), "--seeds", *[str(s) for s in prof.seeds]]
    train.append("--all-variants" if prof.all_variants else "--variant")
    if not prof.all_variants:
        train.append("full")
    run(train)


def _full_adapter(p: ArtifactPaths, prof) -> str:
    """Path of the 'full' adapter under the variant/seed layout train wrote."""
    adir = str(p.adapters)
    if prof.all_variants:
        adir = f"{adir}/full"
    if len(prof.seeds) > 1:
        adir = f"{adir}/seed-{prof.seeds[0]}"
    return adir


def stage_eval(p: ArtifactPaths, prof) -> None:
    run(["scripts/gec/llm_rag_baseline.py", "--input", str(p.real_pairs), "--output", str(p.llm_rag)])
    run(["scripts/gec/predict.py", "--pairs", str(p.llm_rag), "--adapter-dir",
         _full_adapter(p, prof), "--output", str(p.darag_preds), "--column", "gec_pred"])
    run(["scripts/gec/evaluate.py", "--input", str(p.darag_preds), "--prediction-columns",
         "raw_asr", "corrected_text", "gec_pred", "--wer-output", str(p.darag_wer),
         "--ne-f1-output", str(p.darag_ne_f1)])
    run(["scripts/gec/gate.py", "--report", str(p.darag_wer)])
    run(["scripts/gec/export_serve.py", "--adapter-dir", _full_adapter(p, prof),
         "--datastore", str(p.datastore), "--output", str(p.serve_bundle),
         "--gate-report", str(p.darag_wer)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="smoke", choices=["smoke", "full"])
    parser.add_argument("--stage", default="all", choices=list(STAGES))
    parser.add_argument("--dataset", default="tensorxt/ViMedCSS")
    args = parser.parse_args()

    prof = get_profile(args.profile)
    suffix = "" if prof.name == "full" else f"_{prof.name}"
    paths = ArtifactPaths(root=Path("artifacts"), suffix=suffix)

    wanted = STAGES[1:] if args.stage == "all" else [args.stage]
    for stage in wanted:
        print(f"\n===== STAGE: {stage} (profile={prof.name}) =====")
        if stage == "data":
            stage_data(paths, prof, args.dataset)
        elif stage == "synth":
            stage_synth(paths, prof)
        elif stage == "train":
            stage_train(paths, prof)
        elif stage == "eval":
            stage_eval(paths, prof)
    print("\nPipeline stage(s) complete:", ", ".join(wanted))


if __name__ == "__main__":
    main()
