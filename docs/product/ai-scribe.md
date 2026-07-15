# Ghi chép bệnh án AI

## Contract

Ghi chép bệnh án AI listens to a consultation and creates a structured clinical
note draft. It is appropriate when a clinician wants to reduce post-visit data
entry time. The clinician reviews the output before use.

The serving boundary is `scribe/carepath` under `/api/v1/*`. The public site
provides the workflow from `/ghi-chep-lam-sang/`.

## Constraints

- The result is a draft, not independent clinical judgment.
- Uploaded audio is processed in temporary working storage only; it is not a
  durable audio record.
- Provider failures return an explicit failure or configured safe fallback;
  they do not silently invent clinical content.
- Vietnamese copy remains NFC-normalized with diacritics preserved.
- GEC training accepts a dataset only through a versioned manifest with source,
  consent status, and SHA-256. Training is blocked until the owner approves the
  manifest; no clinical audio is collected or stored by this repository flow.
- The committed text-only frozen baseline report is verified in CI. Before an
  adapter can export, its frozen-fixture drug-name recall and dosage
  number/unit preservation must not regress against the raw-ASR baseline.
- In-house SOAP review may use only synthetic or already-approved
  de-identified material. It is informational only and does not authorize a
  SOAP fine-tuning, provider, or safety-policy change. The optional rating
  schema stores no note text or audio here.
- Owner-authorized model development may use public or synthetic research data
  in private Google Colab runtimes. Every dataset and derived artifact must
  carry immutable provenance, usage scope `research_only`, and promotion status
  `blocked_research_only`; this work cannot change the production provider or
  support a clinical-quality claim.
- Research compares the deployed Gipformer baseline, runtime-compatible
  transcript correction, and a direct Vietnamese medical ASR adapter on frozen
  overall, code-switched, medical-term, number, and dosage metrics. Aggregate
  WER alone is not an approval signal.
- A research-only SOAP adapter may be trained from public/synthetic material
  only when each output fact remains grounded to source text. Assessment or
  plan content is copied only when present in the clinician's words; otherwise
  it remains missing. The public `/api/v1/*` schema and `review_required=true`
  contract do not change.
- CarePath consultation audio is never training data. Public benchmark audio
  may exist only in the ephemeral Colab dataset cache and is not committed,
  uploaded to model storage, or saved in resumable checkpoints.

## Proof

The baseline proof is `CP-BASE-001`: root Python tests and the keyless backend
smoke test. A change to the API, audio pipeline, or provider boundary requires
the appropriate story and stronger validation.
