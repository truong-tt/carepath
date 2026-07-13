# Phiên dịch khám bệnh trực tiếp

## Contract

Phiên dịch khám bệnh trực tiếp translates two ways between a Vietnamese-speaking
clinician and an English-speaking patient during a consultation. It is for
people who do not share a language. It translates only and must not provide
medical advice, diagnoses, or treatment recommendations.

The serving boundary is `interpreter/app` under `/api/*` and `/ws/*`, integrated
into the combined FastAPI process. The browser workflow is served at
`/phien-dich-y-khoa/`.

## Safety Invariants

- No microphone capture before recorded consent.
- Raw audio is not persisted; processing is memory-only.
- Low-confidence output is visibly flagged.
- High- and critical-risk turns remain blocked from patient display and TTS
  until clinician confirmation.
- Pipeline or reviewer failure fails closed, showing the clinician the source
  and translation with an escalation path rather than sending content onward.

These are non-negotiable `AGENTS.md` invariants. Changes to them are always
high-risk and require updated fixtures and mock eval proof.
