"""Run the gated CarePath transcript pipeline locally or from generated Colab notebooks.

The default smoke profile is CPU-only and uses committed fixtures. Paid profiles
require ``--confirm-paid`` and an owner-approved dataset manifest before any data
or model step starts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))

from gec.candidates import (  # noqa: E402
    asr_benchmark,
    phonetic_candidate_gate,
    select_transcript_candidate,
)
from gec.cliutil import configure_stdout  # noqa: E402
from gec.data import read_jsonl, write_jsonl  # noqa: E402
from gec.manifest import load_manifest, sha256_file  # noqa: E402
from gec.paths import ArtifactPaths  # noqa: E402
from gec.run_config import load_pipeline_config  # noqa: E402

configure_stdout()

STAGES = ("all", "data", "asr", "synth", "train", "eval")
CONFIGS = {
    "smoke": "smoke-v2.json",
    "pilot": "pilot-v1.json",
    "research-full": "research-full-v1.json",
    "replicate": "replicate-v1.json",
    "reproduction": "reproduction-v1.json",
}


def run(args: list[str]) -> None:
    run_env = dict(os.environ)
    run_env["PYTHONPATH"] = os.pathsep.join(("scribe/training", "scribe"))
    run_env["PYTHONIOENCODING"] = "utf-8"
    printable = " ".join(str(item) for item in args)
    print("\n>>>", printable, flush=True)
    proc = subprocess.run([sys.executable, *map(str, args)], env=run_env, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"step failed ({proc.returncode}): {printable}")


def stage_data(paths: ArtifactPaths, profile, dataset: str, manifest_path: Path) -> None:
    command = [
        "scribe/training/scripts/build_datastore.py",
        "--output",
        str(paths.datastore),
    ]
    if profile.name != "smoke":
        command += [
            "--dataset",
            dataset,
            "--manifest",
            str(manifest_path),
            "--splits",
            "train",
            "--limit-per-split",
            str(profile.limit_per_split or 0),
        ]
    run(command)


def stage_asr(
    paths: ArtifactPaths,
    profile,
    dataset: str,
    frozen_fixture: Path,
    manifest: dict | None,
    manifest_path: Path,
    confirm_paid: bool,
) -> None:
    if profile.name == "smoke":
        _write_smoke_pairs(frozen_fixture, paths.real_pairs)
    else:
        run(
            [
                "scribe/training/scripts/make_pairs.py",
                "--dataset",
                dataset,
                "--manifest",
                str(manifest_path),
                "--output",
                str(paths.real_pairs),
                "--asr-provider",
                profile.asr_provider,
                "--datastore",
                str(paths.datastore),
                "--retrieval-backend",
                profile.retrieval_backend,
                "--train-limit",
                str(profile.limit_per_split or 0),
                "--n-best",
                str(profile.n_best),
                "--resume",
            ]
        )
    rows = read_jsonl(paths.real_pairs)
    report = asr_benchmark(rows, manifest=manifest)
    report["experiment"] = _asr_experiment_contract(profile)
    if profile.enable_direct_asr:
        for seed in profile.seeds:
            is_candidate = seed == profile.candidate_seed
            predictions = (
                paths.asr_predictions
                if is_candidate
                else paths.asr_predictions.with_name(
                    f"{paths.asr_predictions.stem}_seed-{seed}{paths.asr_predictions.suffix}"
                )
            )
            lora_report = (
                paths.asr_lora_report
                if is_candidate
                else paths.asr_lora_report.with_name(
                    f"{paths.asr_lora_report.stem}_seed-{seed}{paths.asr_lora_report.suffix}"
                )
            )
            run(
                [
                    "scribe/training/scripts/train_asr_lora.py",
                    "--dataset",
                    dataset,
                    "--manifest",
                    str(manifest_path),
                    "--baseline-pairs",
                    str(paths.real_pairs),
                    "--output-dir",
                    str(paths.asr_lora_root / f"seed-{seed}"),
                    "--predictions",
                    str(predictions),
                    "--report",
                    str(lora_report),
                    "--max-steps",
                    str(profile.max_steps),
                    "--seed",
                    str(seed),
                    *(["--confirm-paid"] if confirm_paid else []),
                    *(
                        ["--require-near-miss"]
                        if profile.enable_near_miss and is_candidate
                        else []
                    ),
                    *(
                        ["--train-limit", str(profile.limit_per_split)]
                        if profile.limit_per_split
                        else []
                    ),
                ]
            )
            if is_candidate:
                report["direct_asr"] = json.loads(lora_report.read_text(encoding="utf-8"))
    paths.asr_benchmark.parent.mkdir(parents=True, exist_ok=True)
    paths.asr_benchmark.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def stage_synth(paths: ArtifactPaths, profile, *, confirm_reproduction: bool) -> None:
    if not profile.enable_synthetic:
        print(f"Synthetic/TTS stages are disabled for profile '{profile.name}'.")
        return
    if not confirm_reproduction:
        raise ValueError("reproduction/TTS requires explicit --confirm-reproduction")
    if not paths.phonetic_gate.exists():
        raise ValueError("TTS blocked until a prior phonetic-vs-full evaluation gate exists")
    phonetic_evidence = json.loads(paths.phonetic_gate.read_text(encoding="utf-8"))
    if phonetic_evidence.get("accepted") is not True:
        raise ValueError("TTS blocked because the text-only phonetic candidate did not pass")
    count = profile.synth_count
    if count is None:
        count = sum(1 for row in read_jsonl(paths.real_pairs) if row.get("split") == "train")
    generation = [
        "scribe/training/scripts/gen_synthetic.py",
        "--pairs",
        str(paths.real_pairs),
        "--output",
        str(paths.synth_clean),
        "--count",
        str(count),
        "--load-in-4bit",
    ]
    run(generation)
    if not profile.enable_tts:
        return
    tts = [
        "scribe/training/scripts/voice_clone_tts.py",
        "--input",
        str(paths.synth_clean),
        "--output",
        str(paths.tts_manifest),
        "--provider",
        profile.tts_provider,
        "--ref-dataset",
        "tensorxt/ViMedCSS",
        "--ref-count",
        "20",
        "--resume",
    ]
    if profile.synth_tts_limit:
        tts += ["--limit", str(profile.synth_tts_limit)]
    run(tts)
    run(
        [
            "scribe/training/scripts/make_synth_pairs.py",
            "--input",
            str(paths.tts_manifest),
            "--output",
            str(paths.synth_pairs),
            "--datastore",
            str(paths.datastore),
            "--n-best",
            str(profile.n_best),
            "--resume",
        ]
    )
    run(
        [
            "scribe/training/scripts/check_leakage.py",
            "--synthetic",
            str(paths.synth_clean),
            "--real",
            str(paths.real_pairs),
            "--output",
            str(paths.leakage),
        ]
    )


def stage_train(paths: ArtifactPaths, profile) -> None:
    harvest_pairs = [str(paths.real_pairs)]
    if profile.enable_synthetic and paths.synth_pairs.exists():
        harvest_pairs.append(str(paths.synth_pairs))
    run(
        [
            "scribe/training/scripts/harvest_aliases.py",
            "--datastore",
            str(paths.datastore),
            "--pairs",
            *harvest_pairs,
            "--refresh",
            "--mine-split",
            "train",
            "--backend",
            profile.retrieval_backend,
        ]
    )
    augment = [
        "scribe/training/scripts/augment.py",
        "--real",
        str(paths.real_pairs),
        "--output",
        str(paths.augmented),
        "--nsyn-factor",
        str(profile.nsyn_factor),
    ]
    if profile.enable_phonetic:
        augment += ["--phonetic-seed", str(profile.candidate_seed)]
    if profile.enable_synthetic and paths.synth_pairs.exists():
        augment += ["--synthetic", str(paths.synth_pairs)]
    run(augment)
    if profile.train_mode == "mock":
        adapter = _candidate_adapter(paths, profile)
        adapter.mkdir(parents=True, exist_ok=True)
        (adapter / "adapter_config.json").write_text(
            json.dumps({"mock": True, "profile": profile.name}) + "\n", encoding="utf-8"
        )
        (adapter / "darag_variant.json").write_text(
            json.dumps(
                {
                    "variant": profile.candidate_variant,
                    "use_retrieval": True,
                    "seed": profile.candidate_seed,
                    "mock": True,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        print("Created mock adapter marker for orchestration smoke:", adapter)
        return
    train = [
        "scribe/training/scripts/train.py",
        "--pairs",
        str(paths.augmented),
        "--output-dir",
        str(paths.adapters),
        "--max-steps",
        str(profile.max_steps),
        "--seeds",
        *[str(seed) for seed in profile.seeds],
    ]
    if profile.all_variants:
        train.append("--all-variants")
    elif profile.enable_phonetic:
        train += ["--variants", "full", "phonetic"]
    else:
        train += ["--variant", profile.candidate_variant]
    run(train)


def stage_eval(
    paths: ArtifactPaths,
    profile,
    frozen_fixture: Path,
    frozen_manifest: Path,
) -> None:
    adapter = _candidate_adapter(paths, profile)
    if profile.train_mode == "mock":
        _write_mock_predictions(paths.real_pairs, paths.darag_preds)
    else:
        run(
            [
                "scribe/training/scripts/llm_rag_baseline.py",
                "--input",
                str(paths.real_pairs),
                "--output",
                str(paths.llm_rag),
            ]
        )
        prediction_input = paths.llm_rag
        if profile.enable_phonetic:
            full_adapter = paths.candidate_adapter(
                "full",
                profile.candidate_seed,
                all_variants=True,
                multi_seed=len(profile.seeds) > 1,
            )
            run(
                [
                    "scribe/training/scripts/predict.py",
                    "--pairs",
                    str(prediction_input),
                    "--adapter-dir",
                    str(full_adapter),
                    "--output",
                    str(paths.darag_preds),
                    "--column",
                    "gec_full_pred",
                ]
            )
            prediction_input = paths.darag_preds
        run(
            [
                "scribe/training/scripts/predict.py",
                "--pairs",
                str(prediction_input),
                "--adapter-dir",
                str(adapter),
                "--output",
                str(paths.darag_preds),
                "--column",
                "gec_pred",
            ]
        )
    prediction_columns = ["raw_asr", "corrected_text", "gec_pred"]
    phonetic_decision = None
    if profile.enable_phonetic and profile.train_mode != "mock":
        prediction_columns.append("gec_full_pred")
    if paths.asr_predictions.exists():
        _merge_direct_predictions(paths.darag_preds, paths.asr_predictions)
        prediction_columns.append("phowhisper_pred")
    run(
        [
            "scribe/training/scripts/evaluate.py",
            "--input",
            str(paths.darag_preds),
            "--prediction-columns",
            *prediction_columns,
            "--wer-output",
            str(paths.darag_wer),
            "--ne-f1-output",
            str(paths.darag_ne_f1),
            "--stratified-output",
            str(paths.darag_stratified),
        ]
    )
    run(["scribe/training/scripts/gate.py", "--report", str(paths.darag_wer)])

    frozen = load_manifest(frozen_manifest)
    if sha256_file(frozen_fixture) != frozen["sha256"]:
        raise ValueError("frozen evaluation fixture hash does not match its manifest")
    if profile.train_mode == "mock":
        _write_mock_predictions(frozen_fixture, paths.frozen_preds)
    else:
        frozen_input = frozen_fixture
        if profile.enable_phonetic:
            full_adapter = paths.candidate_adapter(
                "full",
                profile.candidate_seed,
                all_variants=True,
                multi_seed=len(profile.seeds) > 1,
            )
            run(
                [
                    "scribe/training/scripts/predict.py",
                    "--pairs",
                    str(frozen_input),
                    "--adapter-dir",
                    str(full_adapter),
                    "--output",
                    str(paths.frozen_preds),
                    "--column",
                    "gec_full_pred",
                ]
            )
            frozen_input = paths.frozen_preds
        run(
            [
                "scribe/training/scripts/predict.py",
                "--pairs",
                str(frozen_input),
                "--adapter-dir",
                str(adapter),
                "--output",
                str(paths.frozen_preds),
                "--column",
                "gec_pred",
            ]
        )
    frozen_columns = ["raw_asr", "gec_pred"]
    if profile.enable_phonetic and profile.train_mode != "mock":
        frozen_columns.append("gec_full_pred")
    run(
        [
            "scribe/training/scripts/evaluate.py",
            "--input",
            str(paths.frozen_preds),
            "--prediction-columns",
            *frozen_columns,
            "--wer-output",
            str(paths.frozen_wer),
            "--ne-f1-output",
            str(paths.frozen_ne_f1),
            "--stratified-output",
            str(paths.frozen_stratified),
        ]
    )
    run(
        [
            "scribe/training/scripts/gate.py",
            "--report",
            str(paths.frozen_wer),
            "--candidate",
            "gec_pred",
            "--baselines",
            "raw_asr",
            "--splits",
            "frozen",
            "--safety-report",
            str(paths.frozen_stratified),
        ]
    )
    if profile.enable_phonetic and profile.train_mode != "mock":
        phonetic_decision = phonetic_candidate_gate(
            json.loads(paths.darag_wer.read_text(encoding="utf-8")),
            json.loads(paths.frozen_stratified.read_text(encoding="utf-8")),
        )
        paths.phonetic_gate.write_text(
            json.dumps(phonetic_decision, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(phonetic_decision, ensure_ascii=False, indent=2))
    latency = {}
    if paths.asr_lora_report.exists():
        direct_report = json.loads(paths.asr_lora_report.read_text(encoding="utf-8"))
        latency["phowhisper_pred"] = direct_report["runtime"].get("real_time_factor")
    selection_metrics = json.loads(paths.darag_wer.read_text(encoding="utf-8"))
    if phonetic_decision is not None and not phonetic_decision["accepted"]:
        selection_metrics.pop("gec_pred", None)
    selection = select_transcript_candidate(
        selection_metrics,
        json.loads(paths.frozen_stratified.read_text(encoding="utf-8")),
        latency_seconds=latency,
        direct_safety_report=direct_report.get("direct_safety", {})
        if paths.asr_lora_report.exists()
        else {},
    )
    if phonetic_decision is not None:
        selection["phonetic_gate"] = phonetic_decision
    paths.candidate_selection.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _mark_asr_selected(paths, profile, selection["selected"])
    print(json.dumps(selection, ensure_ascii=False, indent=2))
    if profile.train_mode == "mock":
        print("Smoke gates passed; mock adapters are never exported as serving models.")
    elif selection["selected"] == "gec_pred":
        run(
            [
                "scribe/training/scripts/export_serve.py",
                "--adapter-dir",
                str(adapter),
                "--datastore",
                str(paths.datastore),
                "--output",
                str(paths.serve_bundle),
                "--normal-gate-report",
                str(paths.darag_wer),
                "--frozen-gate-report",
                str(paths.frozen_wer),
                "--frozen-safety-report",
                str(paths.frozen_stratified),
            ]
        )
    else:
        print(f"GEC export skipped: selected transcript candidate is {selection['selected']!r}.")


def _candidate_adapter(paths: ArtifactPaths, profile) -> Path:
    return paths.candidate_adapter(
        profile.candidate_variant,
        profile.candidate_seed,
        all_variants=profile.all_variants or profile.enable_phonetic,
        multi_seed=len(profile.seeds) > 1,
    )


def _write_smoke_pairs(fixture: Path, output: Path) -> None:
    rows = read_jsonl(fixture)
    splits = ("hard", "validation", "test", "train")
    pairs = [
        {
            **row,
            "split": splits[index % len(splits)],
            "source_kind": "frozen_synthetic_fixture",
            "audio_id": row["id"],
            "retrieved_terms": row.get("gold_terms", []),
            "asr_model": "mock-single-best",
            "duration_seconds": 1.0,
        }
        for index, row in enumerate(rows)
    ]
    write_jsonl(output, pairs)
    print(f"Wrote {len(pairs)} local smoke pairs -> {output}")


def _write_mock_predictions(source: Path, output: Path) -> None:
    rows = [
        {
            **row,
            "corrected_text": row["raw_asr"],
            "gec_pred": row["gold_text"],
            "prediction_provider": "mock-gold-fixture",
        }
        for row in read_jsonl(source)
    ]
    write_jsonl(output, rows)


def _merge_direct_predictions(target: Path, direct_predictions: Path) -> None:
    direct = {
        (str(row.get("split")), str(row.get("audio_id"))): row["phowhisper_pred"]
        for row in read_jsonl(direct_predictions)
    }
    rows = read_jsonl(target)
    merged = [
        {
            **row,
            **(
                {"phowhisper_pred": direct[(str(row.get("split")), str(row.get("audio_id")))]}
                if (str(row.get("split")), str(row.get("audio_id"))) in direct
                else {}
            ),
        }
        for row in rows
    ]
    write_jsonl(target, merged)


def _mark_asr_selected(paths: ArtifactPaths, profile, selected: str) -> None:
    component_path = paths.asr_lora_root / f"seed-{profile.candidate_seed}" / "asr_component.json"
    if not component_path.exists():
        return
    component = json.loads(component_path.read_text(encoding="utf-8"))
    choose_direct = selected == "phowhisper_pred"
    if choose_direct and component.get("gate_accepted") is not True:
        raise ValueError("selection chose a direct ASR component whose independent gate is not accepted")
    component["selected_for_serving"] = choose_direct
    if choose_direct:
        component["selection_report_sha256"] = hashlib.sha256(
            paths.candidate_selection.read_bytes()
        ).hexdigest()
    else:
        component.pop("selection_report_sha256", None)
    temporary = component_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(component, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(component_path)


def _asr_experiment_contract(profile) -> dict:
    return {
        "status": "enabled" if profile.enable_direct_asr else "disabled_for_smoke",
        "candidate": profile.asr_experiment,
        "base_model": "vinai/PhoWhisper-small",
        "train_split": "train",
        "evaluation_splits": ["validation", "test", "hard", "VietMed-test"],
        "plain_lora_gate": {
            "minimum_relative_wer_gain": 0.05,
            "minimum_relative_medical_term_error_gain": 0.05,
        },
        "near_miss_runs_only_after_plain_lora_gate": True,
        "near_miss_implementation_status": (
            "not_implemented_fail_closed" if profile.enable_near_miss else "not_requested"
        ),
        "VietMed-test": "approved_research_evaluation_not_run",
        "candidate_gate": {
            "minimum_relative_hard_wer_gain": 0.10,
            "minimum_relative_hard_medical_term_error_gain": 0.10,
            "maximum_real_time_factor": 1.0,
        },
        "note": (
            "Near-miss is a fail-closed not_implemented blocker if plain LoRA passes."
            if profile.enable_near_miss
            else "Near-miss is not part of this profile."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="smoke", choices=sorted(CONFIGS))
    parser.add_argument("--config", type=Path, help="versioned JSON run config")
    parser.add_argument("--stage", default="all", choices=list(STAGES))
    parser.add_argument(
        "--confirm-paid",
        action="store_true",
        help="explicitly allow a non-smoke profile to consume paid Colab/GPU time",
    )
    parser.add_argument(
        "--confirm-reproduction",
        action="store_true",
        help="explicitly authorize reproduction-only synthetic/TTS after its evidence gate",
    )
    args = parser.parse_args()

    config_path = args.config or Path("scribe/training/configs") / CONFIGS[args.profile]
    config = load_pipeline_config(config_path)
    profile = config.profile
    if profile.paid and not args.confirm_paid:
        raise SystemExit(
            f"Profile '{profile.name}' may consume paid GPU time; inspect the config and rerun "
            "with --confirm-paid."
        )
    manifest = None
    if profile.name != "smoke":
        manifest = load_manifest(config.manifest, require_approved=True)

    artifact_root = Path(os.environ.get("CAREPATH_ARTIFACT_ROOT", config.artifact_root))
    paths = ArtifactPaths(root=artifact_root, suffix=config.suffix)
    wanted = STAGES[1:] if args.stage == "all" else [args.stage]
    for stage in wanted:
        print(f"\n===== STAGE: {stage} (run={config.run_id}, profile={profile.name}) =====")
        if stage == "data":
            stage_data(paths, profile, config.dataset, config.manifest)
        elif stage == "asr":
            stage_asr(
                paths,
                profile,
                config.dataset,
                config.frozen_eval_fixture,
                manifest,
                config.manifest,
                args.confirm_paid,
            )
        elif stage == "synth":
            stage_synth(
                paths,
                profile,
                confirm_reproduction=args.confirm_reproduction
                or os.environ.get("CAREPATH_CONFIRM_REPRODUCTION") == "1",
            )
        elif stage == "train":
            stage_train(paths, profile)
        elif stage == "eval":
            stage_eval(
                paths,
                profile,
                config.frozen_eval_fixture,
                config.frozen_eval_manifest,
            )
    print("\nPipeline stage(s) complete:", ", ".join(wanted))


if __name__ == "__main__":
    main()
