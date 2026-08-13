# 0023 Foreign-patient care navigator, and the patient/clinician language split

Date: 2026-08-13

## Status

Accepted

## Context

CarePath was built as clinic-facing software and its public surface says so: the
landing page addresses a Vietnamese clinic owner, and `AGENTS.md` requires
Vietnamese-first primary labels on every user-facing screen.

The product direction has narrowed. The user CarePath now serves first is a
**foreign tourist or expat seeking outpatient care in Vietnam** — someone who
does not know which clinic to use, cannot prepare for the visit, struggles during
it, and leaves holding Vietnamese paper. That person does not read Vietnamese.
A Vietnamese-first homepage addressed to them is a contradiction, not a courtesy.

Two constraints pull the other way, and both are real:

1. The clinician is still the one who operates the safety gate, and the clinician
   is Vietnamese. Gate cards, risk labels and confirmation actions must not
   become English.
2. `AGENTS.md` §"Product UX contract" mandates Vietnamese-first primary labels
   globally, `App.test.tsx` asserts a Vietnamese hero heading, and
   `scripts/check-diacritics.mjs` fails the build if Vietnamese copy is dropped
   or stripped of diacritics.

## Decision

**Split the language contract by audience rather than applying one rule globally.**

- **Patient-facing surfaces default to English**, with the existing VI toggle:
  `/`, `/get-care/`, `/my-carepath/`, and the patient column of the bilingual
  visit.
- **Clinician-facing surfaces stay Vietnamese-first**: the gate card, risk
  labels, the doctor column, `/ghi-chep-lam-sang/`, `/thu-nghiem/` and
  `/dich-giay-to/`'s clinician review. No English primary labels there.
- Vietnamese copy is never deleted to make room for English. The toggle keeps
  both, and the diacritics gate stays in force.

Alongside it, **the public product is one journey, not a tool menu**. Scribe,
document reading and interpretation are capabilities inside
Find care → Prepare → Visit → Verify → Paperwork → Follow-up, and are not
marketed independently.

## Alternatives Considered

1. **Keep Vietnamese default everywhere, add an EN toggle.** Zero churn, and
   `AGENTS.md` stays literally true. Rejected: the primary user has to find and
   click a toggle before the product's own pitch is readable to them.
2. **Two separate surfaces** — a Vietnamese clinic site and an English patient
   site. Rejected: doubles the copy and the routes to maintain, for a hackathon
   MVP whose whole thesis is that this is *one* journey.
3. **English everywhere.** Rejected: it would put the clinician's safety-critical
   confirmation UI in a language the clinician may not read fluently, which is a
   safety regression dressed as consistency.

## Consequences

Positive:

- The first screen a foreign patient or a judge sees is readable to them.
- The clinician's decision surface is unchanged, so no safety-critical copy moves
  into a second language.
- The pivot is expressible as composition over the existing frontend; no backend,
  schema or API change is required.

Tradeoffs:

- `AGENTS.md`'s global Vietnamese-first clause becomes wrong and must be narrowed
  in the same change, or the contract and the code disagree.
- `App.test.tsx` and `LandingPage.test.tsx` assert Vietnamese landing copy and
  must be updated with the flip rather than after it.
- Two default languages in one app is a standing source of drift. The mitigation
  is that language default is a property of the audience of a route, stated in
  `AGENTS.md`, not a per-component choice.

## Follow-Up

- Narrow the `AGENTS.md` product UX contract to the patient/clinician split.
- Record the journey IA in `docs/ux-redesign-carepath.md` before code changes.
- Story `CP-NAV-01` carries the implementation and its proof.
