# CarePath Colab training notebooks

Five generated notebooks call the same gated orchestrators as the command line.
Edit `scribe/training/scripts/build_notebooks.py`, then regenerate; do not edit
the `.ipynb` files directly.

## Profiles

| Profile | Rows per split | Seeds | Steps | Synthetic/TTS | Purpose |
|---|---:|---|---:|---|---|
| `smoke` | 20 local fixture rows | 13 | 20 mock | no | CPU orchestration check; default |
| `pilot` | up to 1,000 | 13 | 200 | no | first paid candidate |
| `research-full` | all approved rows | 13 | 600 | no | one full-data candidate |
| `replicate` | all approved rows | 13, 7, 42 | 600 | no | reproduce a passing candidate |
| `reproduction` | all approved rows | 13, 7, 42 | 600 | yes | explicit DARAG ablations only |

Paid profiles fail until both conditions are true: the dataset manifest is
owner-approved and `CAREPATH_CONFIRM_PAID=1` is set. Check the profile before
setting that environment variable.

## QLoRA backend

Real paid GEC and SOAP QLoRA default to
`CAREPATH_QLORA_BACKEND=unsloth`. Set it to `hf` to select the reference
Hugging Face/TRL path explicitly. Any other value, or a failure after selecting
Unsloth, stops training; the runner never silently changes backends. The `smoke`
profile remains mock-only and does not install or import Unsloth.

Only paid runs in notebooks 02 and 03 install `training-fast`. That optional
extra pins Unsloth and its compatible Transformers/TRL/Datasets versions so a
resolver update cannot change the GPU trainer unnoticed. Notebooks 00, 01, and
04 stay on `training`; `reproduction` also keeps `training-tts` in every
notebook where it was already required.

## Run order

1. `00_data_prep.ipynb` — datastore, immutable manifest checks, and verified
   train-only MTS-Dialog/ACI-BENCH/MedEV preparation under ephemeral `/content`.
2. `01_asr_benchmark.ipynb` — single-best Gipformer baseline and direct-ASR experiment contract.
3. `02_train_gec.ipynb` — transcript correction candidate.
4. `03_train_soap.ipynb` — grounded SOAP adapter through its sibling orchestrator.
5. `04_evaluate_export_stage.ipynb` — normal/frozen gates, candidate selection and export.

The production Gipformer interface is single-best. The reproduction profile can
create deterministic acoustic perturbation hypotheses, but they are not decoder
beam N-best and are never assumed to exist at serving time.

Artifacts and resumable checkpoints go to
`MyDrive/carepath_artifacts/<run-id>/` on Colab. Dataset audio remains in the
ephemeral runtime cache and is not copied to Drive. The bootstrap reads
`GITHUB_TOKEN` from Colab Secrets or the environment and authenticates through
`GIT_ASKPASS`; the token is never embedded in the clone URL.

Headless equivalent:

```text
python scribe/training/scripts/run_pipeline.py --config scribe/training/configs/smoke-v2.json --stage all
python scribe/training/scripts/run_pipeline.py --config scribe/training/configs/pilot-v1.json --stage all --confirm-paid
```

Verify generated notebooks with:

```text
python scribe/training/scripts/build_notebooks.py --check
```

The owner GPU acceptance run remains pending. For both GEC and SOAP, compare
20 optimizer steps with `hf` and `unsloth` on the same L4, inputs, model
revision, seed, batch size, gradient accumulation, sequence length, and dtype.
Each Unsloth run must improve steps/second by at least 20%. Also retain proof
that a saved adapter reloads in a fresh runtime and that a disconnected run
resumes from its latest Drive checkpoint. Local mock output is not a substitute
for any of this platform evidence.
