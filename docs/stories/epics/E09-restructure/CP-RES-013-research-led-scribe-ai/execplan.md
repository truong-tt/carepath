# Exec Plan

## Goal

Deliver the smallest reproducible, research-led training-to-staging pipeline for
Vietnamese medical transcription correction and grounded SOAP drafting.

## Scope

In scope:

- Verified local paper pack and research-to-design matrix.
- Gated Colab profiles and generated notebooks.
- Mock/CPU ASR and GEC candidate comparison with GPU command paths.
- Public/synthetic grounded SOAP preparation, evaluation, and research bundle.
- Private in-process staging smoke with unchanged production behavior.
- Explicit Unsloth/HF QLoRA selection with pinned, training-only acceleration
  dependencies and generated-notebook routing.

Out of scope:

- Patient data, public serving, production promotion, TTS-first augmentation,
  exhaustive paper ablations, clinical validation, or Interpreter changes.

## Risk Classification

Risk flags:

- Model training, public dataset rights, provider usage, medical-note safety,
  artifact promotion, and private Colab credentials.

Hard gates:

- Unapproved or unhashed manifests stop model stages.
- Test/hard splits never enter training or retrieval datastores.
- Critical unsupported SOAP facts and medication/dose/number/negation regressions
  stop export.
- Research bundles cannot identify themselves as production-promotable.
- Invalid backend selection and any selected-backend failure stop training; no
  silent Unsloth-to-HF fallback is allowed.
- Acceleration is not accepted until both GEC and SOAP improve 20-step
  steps/second by at least 20% on matched owner-run L4 comparisons.

## Work Phases

1. Record the research contract and evidence.
2. Repair shared orchestration and notebook generation.
3. Add ASR/GEC candidate metrics and gates.
4. Add grounded SOAP smoke and Colab training paths.
5. Export/reload a research bundle and run regressions.
6. Record real proof and remaining Colab-only evidence.

## Current Unsloth implementation

- Keep CarePath runtime dependencies unchanged. Add exact GPU trainer pins only
  in the optional `training-fast` extra.
- Default real paid GEC/SOAP QLoRA to `CAREPATH_QLORA_BACKEND=unsloth`; retain
  `hf` only as an explicit operator choice. Mock paths stay lightweight.
- Generate notebooks 02 and 03 so paid profiles install `training-fast`.
  Notebooks 00, 01, and 04 stay on `training`; `reproduction` still includes
  `training-tts`.
- Branch only Qwen model and LoRA construction. Prompts, datasets, model
  revisions, seeds, batch/accumulation semantics, checkpoint cadence,
  `packing=False`, and standard PEFT/tokenizer/task metadata stay unchanged.
- Record each real run before setup and finalize it after success or failure.
  Resume is locked to the recorded backend; only checkpoints with no run
  metadata at all are treated as legacy HF checkpoints.
- Prove dependency, notebook, mock-pipeline, and fail-closed resume policy
  locally. Leave performance, fresh-runtime adapter reload, and
  Drive-checkpoint resume as pending owner-run Colab proof.

## Stop Conditions

Pause if implementation would require patient data, weakening a frozen safety
gate, publishing a model endpoint, changing the public API, or claiming clinical
readiness without a separate owner decision.
