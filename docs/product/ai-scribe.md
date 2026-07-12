# Ghi chép bệnh án AI

## Contract

Ghi chép bệnh án AI listens to a consultation and creates a structured clinical
note draft. It is appropriate when a clinician wants to reduce post-visit data
entry time. The clinician reviews the output before use.

The serving boundary is `apps/api/carepath` under `/api/v1/*`. The public site
provides the workflow from `/ghi-chep-lam-sang/`.

## Constraints

- The result is a draft, not independent clinical judgment.
- Uploaded audio is processed in temporary working storage only; it is not a
  durable audio record.
- Provider failures return an explicit failure or configured safe fallback;
  they do not silently invent clinical content.
- Vietnamese copy remains NFC-normalized with diacritics preserved.

## Proof

The baseline proof is `CP-BASE-001`: root Python tests and the keyless backend
smoke test. A change to the API, audio pipeline, or provider boundary requires
the appropriate story and stronger validation.
