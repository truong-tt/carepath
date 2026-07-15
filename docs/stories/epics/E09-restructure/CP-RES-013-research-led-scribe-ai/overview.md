# Overview

## Current Behavior

CarePath has a governed DARAG-inspired GEC training package, generated Colab
notebooks, a frozen transcript safety gate, and prompt-based SOAP serving. The
notebooks can bypass command-line governance, the full profile schedules costly
paper ablations before a pilot, and there is no durable literature synthesis,
direct ASR comparison, or research-only SOAP training path.

## Target Behavior

Provide a reproducible paper pack and a Colab-first research pipeline that
compares direct ASR adaptation with runtime-compatible GEC, trains one grounded
SOAP adapter from public/synthetic data, exports only safety-gated research
bundles, and proves the complete flow with CPU/mock smoke tests.

## Affected Users

- The owner can run resumable research experiments on Colab Pro.
- Engineers can reproduce paper downloads, manifests, smoke runs, metrics, and
  bundle gates without a local NVIDIA GPU.

## Affected Product Docs

- `docs/product/ai-scribe.md`
- `docs/decisions/0018-research-only-scribe-model-development.md`

## Owner Data Approval

On 2026-07-13 the owner approved the listed public datasets for private,
research-only use. The approval is recorded in immutable manifests and excludes
patient data, clinical use, production, and commercial promotion.

## Non-Goals

- Change production providers, public API shapes, UI, Interpreter behavior, or
  deployment.
- Persist CarePath consultation audio or claim clinical/model readiness.
- Run real GPU training from this implementation environment.
