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

## Proof

The baseline proof is `CP-BASE-001`: root Python tests and the keyless backend
smoke test. A change to the API, audio pipeline, or provider boundary requires
the appropriate story and stronger validation.
