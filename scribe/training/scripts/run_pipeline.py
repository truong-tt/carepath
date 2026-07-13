"""CLI: run the DARAG pipeline end-to-end (or a single stage) for a profile.

    # plumbing check (mock ASR, tiny limits, no models needed):
    python scribe/training/scripts/run_pipeline.py --profile smoke --stage data

    # real ViMedCSS run on a GPU box:
    python scribe/training/scripts/run_pipeline.py --profile full --stage all

Stages: ``data`` (datastore + real pairs), ``synth`` (synthetic
transcripts + TTS + synthetic pairs + leakage), ``train`` (augment + QLoRA), and
``eval`` (LLM/RAG baseline + predict + tables + gate). Each stage is independently
runnable and resumable; ``all`` runs them in order. Paths and run-sizes come from
the versioned JSON run config, while ``gec.paths`` derives its artifact names.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe" / "training"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scribe"))

from gec.cliutil import configure_stdout  # noqa: E402

configure_stdout()

from gec.data import read_jsonl  # noqa: E402
from gec.manifest import load_manifest, sha256_file  # noqa: E402
from gec.paths import ArtifactPaths  # noqa: E402
from gec.run_config import load_pipeline_config  # noqa: E402

STAGES = ("all", "data", "synth", "train", "eval")
def run(args: list) -> None:
    run_env = dict(os.environ)
    run_env["PYTHONPATH"] = os.pathsep.join(("scribe/training", "scribe"))
    run_env["PYTHONIOENCODING"] = "utf-8"
    printable = " ".join(str(a) for a in args)
    print("\n>>>", printable, flush=True)
    proc = subprocess.run([sys.executable, *map(str, args)], env=run_env)
    if proc.returncode != 0:
        raise SystemExit(f"step failed ({proc.returncode}): {printable}")


def stage_data(p: ArtifactPaths, prof, dataset: str) -> None:
    limit = str(prof.limit_per_split or 0)
    run(["scribe/training/scripts/build_datastore.py", "--dataset", dataset,
         "--limit-per-split", limit, "--output", str(p.datastore)])
    run(["scribe/training/scripts/make_pairs.py", "--dataset", dataset, "--output", str(p.real_pairs),
         "--asr-provider", prof.asr_provider, "--datastore", str(p.datastore),
         "--retrieval-backend", prof.retrieval_backend, "--limit-per-split", limit,
         "--n-best", str(prof.n_best), "--resume"])
def stage_synth(p: ArtifactPaths, prof) -> None:
    count = prof.synth_count
    if count is None:  # paper nsyn = n: match the real train size
        count = sum(1 for r in read_jsonl(p.real_pairs) if r.get("split") == "train") or 50
    gen = ["scribe/training/scripts/gen_synthetic.py", "--pairs", str(p.real_pairs),
           "--output", str(p.synth_clean), "--count", str(count)]
    if prof.name != "smoke":
        gen.append("--load-in-4bit")
    run(gen)
    tts = ["scribe/training/scripts/voice_clone_tts.py", "--input", str(p.synth_clean),
           "--output", str(p.tts_manifest), "--provider", prof.tts_provider,
           "--ref-dataset", "tensorxt/ViMedCSS", "--ref-count", "20", "--resume"]
    if prof.synth_tts_limit:
        tts += ["--limit", str(prof.synth_tts_limit)]
    run(tts)
    run(["scribe/training/scripts/make_synth_pairs.py", "--input", str(p.tts_manifest),
         "--output", str(p.synth_pairs), "--datastore", str(p.datastore),
         "--n-best", str(prof.n_best), "--resume"])
    run(["scribe/training/scripts/check_leakage.py", "--synthetic", str(p.synth_clean),
         "--real", str(p.real_pairs), "--output", str(p.leakage)])


def stage_train(p: ArtifactPaths, prof) -> None:
    real_inputs = [str(p.real_pairs)]
    # Learn real ASR confusions (paper Limitation #1) into the datastore, then
    # refresh every pair's retrieved NEs so the RAC prompt carries the right term.
    harvest_pairs = list(real_inputs)
    if p.synth_pairs.exists():
        harvest_pairs.append(str(p.synth_pairs))
    run(["scribe/training/scripts/harvest_aliases.py", "--datastore", str(p.datastore),
         "--pairs", *harvest_pairs, "--refresh", "--backend", prof.retrieval_backend])
    run(["scribe/training/scripts/augment.py", "--real", *real_inputs, "--synthetic", str(p.synth_pairs),
         "--output", str(p.augmented), "--nsyn-factor", str(prof.nsyn_factor)])
    train = ["scribe/training/scripts/train.py", "--pairs", str(p.augmented), "--output-dir", str(p.adapters),
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


def stage_eval(p: ArtifactPaths, prof, frozen_fixture: Path, frozen_manifest: Path) -> None:
    run(["scribe/training/scripts/llm_rag_baseline.py", "--input", str(p.real_pairs), "--output", str(p.llm_rag)])
    run(["scribe/training/scripts/predict.py", "--pairs", str(p.llm_rag), "--adapter-dir",
         _full_adapter(p, prof), "--output", str(p.darag_preds), "--column", "gec_pred"])
    run(["scribe/training/scripts/evaluate.py", "--input", str(p.darag_preds), "--prediction-columns",
         "raw_asr", "corrected_text", "gec_pred", "--wer-output", str(p.darag_wer),
         "--ne-f1-output", str(p.darag_ne_f1), "--stratified-output", str(p.darag_stratified)])
    run(["scribe/training/scripts/gate.py", "--report", str(p.darag_wer)])
    frozen = load_manifest(frozen_manifest)
    if sha256_file(frozen_fixture) != frozen["sha256"]:
        raise ValueError("frozen evaluation fixture hash does not match its manifest")
    run(["scribe/training/scripts/predict.py", "--pairs", str(frozen_fixture), "--adapter-dir",
         _full_adapter(p, prof), "--output", str(p.frozen_preds), "--column", "gec_pred"])
    run(["scribe/training/scripts/evaluate.py", "--input", str(p.frozen_preds), "--prediction-columns",
         "raw_asr", "gec_pred", "--wer-output", str(p.frozen_wer), "--ne-f1-output",
         str(p.frozen_ne_f1), "--stratified-output", str(p.frozen_stratified)])
    run(["scribe/training/scripts/gate.py", "--report", str(p.frozen_wer), "--candidate", "gec_pred",
         "--baselines", "raw_asr", "--splits", "frozen", "--safety-report",
         str(p.frozen_stratified)])
    run(["scribe/training/scripts/export_serve.py", "--adapter-dir", _full_adapter(p, prof),
         "--datastore", str(p.datastore), "--output", str(p.serve_bundle),
         "--gate-report", str(p.darag_wer)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="smoke", choices=["smoke", "full"])
    parser.add_argument("--config", type=Path, help="versioned JSON run config")
    parser.add_argument("--stage", default="all", choices=list(STAGES))
    args = parser.parse_args()

    config_path = args.config or Path("scribe/training/configs") / f"{args.profile}-v1.json"
    config = load_pipeline_config(config_path)
    prof = config.profile
    paths = ArtifactPaths(root=config.artifact_root, suffix=config.suffix)

    wanted = STAGES[1:] if args.stage == "all" else [args.stage]
    if "train" in wanted:
        load_manifest(config.manifest, require_approved=True)
    for stage in wanted:
        print(f"\n===== STAGE: {stage} (run={config.run_id}, profile={prof.name}) =====")
        if stage == "data":
            stage_data(paths, prof, config.dataset)
        elif stage == "synth":
            stage_synth(paths, prof)
        elif stage == "train":
            stage_train(paths, prof)
        elif stage == "eval":
            stage_eval(paths, prof, config.frozen_eval_fixture, config.frozen_eval_manifest)
    print("\nPipeline stage(s) complete:", ", ".join(wanted))


if __name__ == "__main__":
    main()
