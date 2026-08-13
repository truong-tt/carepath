# Phiên dịch khám bệnh trực tiếp

## Contract

Phiên dịch khám bệnh trực tiếp translates two ways between a Vietnamese-speaking
clinician and an English-speaking patient during a consultation. It is for
people who do not share a language. It translates only and must not provide
medical advice, diagnoses, or treatment recommendations.

The serving boundary is `interpreter/app` under `/api/*` and `/ws/*`, integrated
into the combined FastAPI process.

## Public availability

This section previously said the web Interpreter was unavailable and that Scribe
was the only public product. That has not been true since the bilingual visit
shipped, and it is corrected here.

The capability **is** publicly served, through two routes in
`scribe/frontend/`:

- `/kham-song-ngu/` — the bilingual visit, including the clinician gate.
- `/dich-giay-to/` — the document reader, which puts every line of Vietnamese
  paperwork through the same risk engine and the same confirmation step.

What remains closed is the **standalone interpreter console**, which was deleted
once the visit screen replaced it. `/phien-dich-y-khoa/*` and `/console/*` are
deliberate 404s and stay that way; there is no separate interpreter frontend in
this repository.

The interpreter **module** is otherwise on hold: accept bug fixes, safety fixes
and required operational maintenance, and leave new product work to the routes
above until the owner reopens it.

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
