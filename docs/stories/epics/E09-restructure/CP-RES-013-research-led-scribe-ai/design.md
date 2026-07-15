# Design

## Domain Model

- A paper record contains provenance, status, license, evidence, limitation,
  CarePath hypothesis, experiment, local filename, and SHA-256.
- An experiment config names a governed dataset manifest, profile, candidate,
  seed, limits, gates, and artifact directory.
- A grounded SOAP fact contains type, value, negation/uncertainty, and exact
  source span. A writer may use only accepted facts.
- Every exported bundle declares `usage_scope=research_only` and
  `promotion_status=blocked_research_only`.

## Application Flow

1. Download and verify papers; approve public/synthetic dataset manifests.
2. Establish Gipformer and mock baselines on frozen splits.
3. Compare direct ASR adapters and single-best GEC/RAC candidates.
4. Prepare provenance-preserving SOAP examples, reject ungrounded rows, and
   train one two-task QLoRA adapter.
5. Evaluate safety-weighted metrics, export a research bundle, reload it in a
   fresh Colab runtime, and call the existing FastAPI interface in process.

## Interface Contract

Public `/api/v1/*` routes and response DTOs are unchanged. Internal staging may
select `LLM_PROVIDER=scribe_local` and `SCRIBE_BUNDLE_PATH`; it must report the
effective provider and fail rather than silently attribute fallback output to a
trained adapter.

## Data Model

No database migration. Research text, metrics, manifests, and model artifacts
remain outside production data stores. Public benchmark audio is ephemeral and
never included in Drive checkpoints or exported bundles.

## UI / Platform Impact

Five generated notebooks separate CPU preparation, ASR benchmarking, GEC
training, SOAP training, and evaluation/staging. Paid profiles require explicit
confirmation; smoke remains the default.

## Observability

Each run records config/manifest hashes, effective candidate and seed, exact
model revisions, metric reports, gate failures, runtime/VRAM where available,
and bundle hashes.

## Alternatives Considered

1. GEC-only research: rejected because direct Vietnamese code-switch ASR papers
   provide a credible competing hypothesis.
2. Multi-model SOAP extraction and writing: rejected because one shared adapter
   with two tasks is sufficient for the pilot.
3. TTS-first augmentation: deferred until cheaper text-only corruption passes.
