# CarePath Scribe research pipeline

This package is the training-to-private-staging path for Vietnamese medical
transcription and grounded SOAP notes. It is research-only: it does not change
the production provider, persist CarePath consultation audio, or authorize a
model for clinical use.

Start with the evidence and limitations in
[`../research/README.md`](../research/README.md). The five generated Colab
notebooks are documented in [`notebooks/README.md`](notebooks/README.md).

## Pipeline

1. Validate data rights, immutable source revisions, split fingerprints, and
   frozen manifests.
2. Benchmark the current single-best Gipformer output and direct PhoWhisper LoRA
   on untouched ViMedCSS evaluation splits. The near-miss contract is recorded,
   but its sequence-ranking trainer remains fail-closed after the plain LoRA gate
   instead of approximating the paper with non-equivalent hypotheses or loss.
3. Compare Gipformer alone, real-error GEC with lexical RAC, and GEC with a
   balanced clean/PiDA-style phonetic mixture. TTS remains locked until the
   text-only candidate passes.
4. Translate/adapt MTS-Dialog and ACI-BENCH training rows with the deterministic
   CKey teacher, reject ungrounded rows, and train one Qwen3-4B QLoRA adapter for
   fact extraction and grounded SOAP writing.
5. Evaluate critical facts and frozen safety cases, assemble independently
   accepted transcript and SOAP components, reload the bundle with FastAPI
   `TestClient`, and optionally upload it to a private Hugging Face model repo.

Candidate metrics and mock smoke results are evidence about orchestration only.
They are never substituted for real Colab WER, PIER, latency, VRAM, or model
quality evidence.

## Colab setup

Use a private Colab notebook with a GPU runtime. Add these values through Colab
Secrets and enable notebook access for each secret:

- `GITHUB_TOKEN`: read access to the private CarePath repository.
- `LLM_API_KEY`: CKey access for paid SOAP data preparation and the independent
  teacher baseline.
- `HF_TOKEN`: access to the destination private Hugging Face model repository.

Do not place tokens in `CAREPATH_REPO_URL`, notebook source, output cells, or Git
remote URLs. The bootstrap uses `GIT_ASKPASS` and keeps public research audio in
the ephemeral `/content` cache. Checkpoints and accepted text/model artifacts go
to `MyDrive/carepath_artifacts/`.

The owner approved the listed public datasets for private research-only use on
2026-07-13. ViMedCSS, VietMed, MTS-Dialog, ACI-BENCH, MedEV, and the Qwen base
model are pinned to exact revisions and hashes. Notebook 00 re-verifies those
locks and prepares the public SOAP text under ephemeral `/content/carepath_data`;
source drift fails closed. This approval does not cover patient data, clinical
use, production, commercial promotion, or the unresolved MedEV repository
license.

Select a profile before running the notebooks in numeric order:

```python
import os

os.environ["CAREPATH_PROFILE"] = "pilot"  # smoke, pilot, research-full, replicate
os.environ["CAREPATH_CONFIRM_PAID"] = "1"
os.environ["CAREPATH_QLORA_BACKEND"] = "unsloth"  # default; use "hf" explicitly
```

`smoke` is the default and needs no paid confirmation. `reproduction` is a
separate paper-ablation profile; it additionally requires accepted PiDA evidence
and explicit reproduction confirmation before synthetic/TTS work. Its near-miss
stage currently exits with a structured `not_implemented` blocker if the plain
LoRA gate passes; it never claims a contrastive result.

### QLoRA backend and dependency boundary

`CAREPATH_QLORA_BACKEND` accepts exactly `unsloth` or `hf`. Real paid GEC and
SOAP QLoRA default to `unsloth`; `hf` is the explicit reference-backend opt-out.
Invalid values fail immediately. An Unsloth import, setup, resume, or training
failure also fails the selected run instead of silently retrying with HF, so the
recorded backend and timing remain trustworthy. Mock training remains
lightweight and does not require the fast stack.

The optional `training-fast` extra pins `unsloth==2026.7.2`,
`unsloth-zoo==2026.7.2`, `transformers==4.56.2`, `trl==0.22.2`, and
`datasets[audio]==4.3.0`. These packages move together at the trainer/model
boundary, so exact pins avoid an unreviewed compatibility combination. They are
not runtime dependencies: only paid QLoRA cells in notebooks 02 and 03 install
the extra. The normal `training` extra remains sufficient for mock/CPU work and
notebooks 00, 01, and 04. The `reproduction` profile still adds `training-tts`.

## Local proof

Run local checks with the repository Python 3.12 environment:

```powershell
.\.venv\Scripts\python.exe scribe/research/download_papers.py --check
.\.venv\Scripts\python.exe -m pytest scribe/training/tests
.\.venv\Scripts\python.exe scribe/training/scripts/build_notebooks.py --check
.\.venv\Scripts\python.exe scribe/training/scripts/baseline_report.py --check
.\.venv\Scripts\python.exe scribe/training/scripts/run_pipeline.py --config scribe/training/configs/smoke-v2.json --stage all
.\.venv\Scripts\python.exe scribe/training/scripts/run_soap_pipeline.py --config scribe/training/configs/soap-smoke-v1.json --stage all
```

The smoke profile uses frozen synthetic fixtures and mock adapters. Mock
artifacts are deliberately refused by the serving-bundle exporters.

## Owner L4 acceptance (pending)

Run the following proof separately for GEC and SOAP; local mock checks cannot
satisfy it:

1. Make two temporary 20-step configs that differ only in run/output identity.
2. On the same Colab L4, run one with `CAREPATH_QLORA_BACKEND=hf` and one with
   `CAREPATH_QLORA_BACKEND=unsloth`. Keep the input rows and order, exact base
   revision, seed, batch size, gradient accumulation, sequence length, dtype,
   and runtime image fixed.
3. Record GPU identity, runtime image, wall time, steps/second, peak VRAM, exact
   package versions, and SHA-256 hashes for the config, data manifest,
   checkpoints, saved adapter, and generated `training_run.json`. For fixed
   20-step runs, calculate
   `((unsloth_steps_per_second / hf_steps_per_second) - 1) * 100`; both GEC and
   SOAP must be at least 20%.
4. Start a fresh L4 runtime, reinstall the pinned extras, load each saved
   Unsloth adapter from Drive without the original trainer object, and run the
   existing prediction/evaluation stage.
5. For each task, run long enough to write a checkpoint, interrupt the runtime,
   reconnect, and verify the same backend resumes from the latest checkpoint
   without changing the locked base revision.

Keep the benchmark logs, adapter-reload output, and before/after checkpoint
paths with the story validation record. Until they are recorded, acceleration,
reload, and resume platform proof remain pending.

## Private upload

Notebook 04 assembles and stages only components that independently passed their
gates. Publishing remains a separate, explicit action:

```powershell
python scribe/training/scripts/publish_scribe_bundle.py `
  --bundle /content/drive/MyDrive/carepath_artifacts/<run-id>/accepted_scribe_bundle `
  --repo-id tranth3truong/carepath-scribe-research `
  --confirm-private-upload
```

The uploader verifies the research bundle and refuses a public destination.
Production promotion still requires a separate data-rights decision, qualified
Vietnamese clinician review, and an explicit rollout decision.
