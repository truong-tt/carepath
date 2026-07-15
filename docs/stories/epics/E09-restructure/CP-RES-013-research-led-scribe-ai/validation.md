# Validation

## Proof Strategy

CPU/mock proof must cover paper verification, governance refusal, deterministic
candidate metrics, SOAP fact grounding, safety rejection, bundle labels, generated
notebook drift, exact fast-extra pins, paid-only notebook routing, absence of
embedded notebook secrets, and existing Scribe regressions. Real WER, PIER,
latency, VRAM, backend speed, adapter training, Drive resume, and fresh-GPU
reload remain Colab evidence.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Paper hashes; profiles; fast-extra pins; ASR metrics; fact alignment; critical SOAP gates |
| Integration | GEC and SOAP smoke pipelines; bundle export/reload; provider identity |
| E2E | Existing keyless Scribe API smoke and unchanged response schema |
| Platform | Generated notebook routing; fresh Colab bootstrap; paid confirmation; adapter reload; Drive resume |
| Performance | Matched 20-step HF/Unsloth L4 runs for GEC and SOAP; wall time, steps/second, peak VRAM |
| Logs/Audit | Config, manifest, model, metric, and bundle hashes |

## Fixtures

- Existing frozen GEC fixture and report.
- Synthetic Vietnamese outpatient dialogue/SOAP rows with medication, dosage,
  number, unit, negation, missing assessment/plan, and unsupported-fact cases.
- Mock ASR candidate predictions for deterministic selection.

## Commands

```text
python scribe/research/download_papers.py --check
python -m pytest scribe/training/tests
python -m pytest scribe/training/tests/test_governance.py
python scribe/training/scripts/build_notebooks.py --check
python scribe/training/scripts/baseline_report.py --check
python scribe/training/scripts/prepare_public_sources.py --manifest scribe/training/manifests/soap-public-v1.json --canonical shared/carepath_shared/terms/medical_terms.json --output-root <ephemeral-cache>
python scribe/training/scripts/run_pipeline.py --config scribe/training/configs/smoke-v2.json --stage all
python scribe/training/scripts/run_soap_pipeline.py --config scribe/training/configs/soap-smoke-v1.json --stage all
python -m pytest
python scripts/smoke_backend.py
python scripts/build_term_artifacts.py --check
ruff check scribe/training/scripts/build_notebooks.py scribe/training/tests/test_governance.py
```

## Unsloth acceleration evidence

Local implementation proof completed on 2026-07-15:

- [x] `training-fast` contains the five exact accepted pins and Unsloth remains
  outside runtime dependencies.
- [x] Generated notebooks are current; only paid paths in notebooks 02 and 03
  add `training-fast`; `reproduction` still adds `training-tts`.
- [x] Governance tests cover routing and reject stored output, credential URLs,
  and common literal GitHub/Hugging Face/API token forms.
- [x] Backend and resume coverage passed: GEC 45 tests and SOAP 18 tests,
  including default/validation, explicit HF selection, same-backend resume,
  legacy-HF handling, malformed-metadata refusal, and cross-backend refusal.
- [x] Run metadata is written before QLoRA setup and finalized on success or
  failure with backend, package, revision, seed, device/dtype, resume, runtime,
  throughput, peak-VRAM, and completion fields.
- [x] Full training package: 99 passed, 1 skipped because it requires a real
  Gipformer decode artifact. Both GEC and SOAP mock pipelines passed.
- [x] Focused governance: 15 passed. Notebook and frozen-baseline drift checks:
  current. Root regressions: 60 passed with one existing Starlette/httpx
  deprecation warning. Backend smoke, term-artifact check, Ruff, and
  `git diff --check` passed.

Owner-run Colab proof is intentionally pending:

| Task | HF 20-step steps/s | Unsloth 20-step steps/s | Improvement | Peak VRAM | GPU/runtime/packages | Artifact SHA-256 | Adapter reload | Drive resume |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| GEC | pending | pending | pending (must be >=20%) | pending | pending | pending | pending | pending |
| SOAP | pending | pending | pending (must be >=20%) | pending | pending | pending | pending | pending |

Both comparisons must use the same L4, inputs and order, exact model revision,
seed, batch size, gradient accumulation, sequence length, dtype, and runtime
image. Improvement is
`((unsloth_steps_per_second / hf_steps_per_second) - 1) * 100`. Adapter proof
requires a fresh runtime with no original trainer object. Resume proof requires
an interrupted paid run to continue from its latest Drive checkpoint. Do not
replace these fields with local mock timings. Each row must retain the GPU
identity, runtime image, exact package versions, peak VRAM, and SHA-256 hashes
for its config, data manifest, checkpoints, saved adapter, and
`training_run.json`.

The local Harness registry returned no present `gpu-training` provider, so the
Colab comparison was cleanly skipped rather than simulated.

## Acceptance Evidence

Local proof completed on 2026-07-13 with the repository Python 3.12 environment:

- Paper verification: 12/12 PDFs present with matching SHA-256 hashes.
- Training package: 85 passed, 1 skipped. The skip requires a real trained
  artifact and is not replaced by mock evidence.
- Public SOAP sources: exact MTS-Dialog and ACI-BENCH train files verified; exact
  MedEV bilingual files produced a deterministic 175-row canonical terminology
  extract with a pinned hash.
- Generated notebooks and frozen baseline report: current.
- Transcript smoke: all five stages passed on 12 frozen synthetic fixture rows;
  the mock adapter was not exported.
- SOAP smoke: 4 rows prepared, 0 rejected, deterministic gate accepted, and a
  mock research bundle exported for structural validation only.
- Scribe/combined regressions: 60 passed with one existing Starlette/httpx
  deprecation warning.
- Backend smoke: health `ok`, mock ASR identified, and `review_required=true`.
- Generated medical-term artifacts: current.
- Ruff over Scribe training, research, runtime, and tests: passed.
- `git diff --check`: passed (line-ending conversion warnings only).
- Student briefs: Phương, Sơn and Kiên each have a compact 42–47-line,
  six-week plan; UTF-8/NFC and secret-pattern checks passed.

No paid Colab GPU training, real WER/PIER, VietMed evaluation, Drive reconnect,
fresh-GPU bundle reload, or Hugging Face upload was run locally. ViMedCSS,
VietMed, MTS-Dialog, ACI-BENCH, and MedEV are approved only for private research,
and their manifests pin exact source revisions and hashes. Colab re-verifies the
locks and fails closed on drift. Clinical, production, and commercial promotion
remain blocked.

The paper's near-miss contrastive trainer is not implemented. The reproduction
profile records the genuine beam/POI/filter/loss contract and exits nonzero with
`not_implemented` after a passing plain-LoRA gate, so it cannot claim an
approximate or fabricated reproduction result.
