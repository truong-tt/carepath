# 0018 Research-Only Scribe Model Development

Date: 2026-07-13

## Status

Accepted

## Context

The owner requested a research-led Vietnamese medical Scribe pipeline covering
papers, direct ASR adaptation, runtime-compatible GEC, grounded SOAP training,
and private Colab staging. Existing decisions authorize GEC governance and
safety gates, while decision 0017 deliberately prevented optional in-house
review from implicitly authorizing SOAP fine-tuning.

On 2026-07-13 the owner stated, "I approve research-only use of the listed
public datasets." This approves private research with ViMedCSS, VietMed,
MTS-Dialog, ACI-BENCH, and MedEV. Public availability and this approval do not
prove commercial data rights, and synthetic or translated SOAP supervision does
not establish clinical validity.

## Decision

Authorize public/synthetic, research-only Scribe model development in private
Google Colab runtimes under story CP-RES-013.

- Compare the current Gipformer baseline, single-best GEC/RAC, and direct
  Vietnamese medical ASR adapters on frozen overall and safety-weighted metrics.
- Permit one Qwen3-4B QLoRA SOAP adapter used in two grounded passes: extract
  source-supported facts, then write the existing SOAP schema from those facts.
- Require immutable data manifests, source split provenance, artifact hashes,
  and the labels `usage_scope=research_only` and
  `promotion_status=blocked_research_only`.
- Keep public benchmark audio in ephemeral Colab caches only. No CarePath
  consultation audio, transcript, note, or identifier enters training.
- Keep production providers, deployments, public routes, and response schemas
  unchanged. Staging uses an in-process FastAPI client in Colab, not a public
  endpoint.
- Pin each public source to an immutable commit and verified hashes. Use
  `tranth3truong/carepath-scribe-research` only as the private accepted-bundle
  destination after an explicit upload command; this decision does not perform
  or authorize public publication.

MedEV's paper describes research and educational availability, but its dataset
repository does not declare a standard license. VietMed's Hugging Face card and
paper also present different license labels. Both therefore remain research-only
and blocked from commercial or production promotion pending a separate rights
decision.

This decision supersedes decision 0017 only where it said in-house work could
not authorize SOAP fine-tuning. Decision 0017's privacy boundary and prohibition
on clinical-readiness claims remain in force.

## Consequences

- CPU/mock smoke tests can prove governance and safety logic locally; real model
  metrics require owner-run Colab GPU evidence.
- A successful research bundle still cannot be promoted without a separate data
  rights decision, qualified Vietnamese clinician review, and production rollout
  decision.
- ROUGE and LLM judges remain diagnostic only. Unsupported critical facts,
  medication/dose corruption, number/unit corruption, or negation corruption
  block export.

## Alternatives Considered

1. Keep prompt-only SOAP indefinitely: rejected because it cannot test the
   approved research hypothesis.
2. Train a single end-to-end speech-to-note model: rejected because it weakens
   attribution, comparison, and fail-closed safety evidence.
3. Reproduce every paper ablation first: rejected because pilot evidence should
   determine whether expensive experiments are warranted.
