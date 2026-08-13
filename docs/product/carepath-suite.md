# CarePath Suite

CarePath is an AI-first care navigator for foreign tourists and expats seeking
outpatient care in Vietnam. It is **one journey**, and its capabilities are
steps inside that journey rather than products sold separately:

```text
Find care → Prepare → Visit → Verify → Paperwork → Follow-up
```

`Verify` is the differentiator and the reason the rest exists. Content carrying
a drug name, a dose or an allergy is withheld from the patient until a clinician
confirms it.

## Surfaces

| Route | What it is | Primary reader |
| --- | --- | --- |
| `/` | The journey, stated once | Foreign patient; a Vietnamese clinic owner behind the toggle |
| `/get-care/` | Need → clinic → visit brief → visit → paperwork | Foreign patient |
| `/my-carepath/` | One care episode, and the control to delete it | Foreign patient |
| `/kham-song-ngu/` | The bilingual visit and the clinician gate | Clinician, with the patient beside them |
| `/dich-giay-to/` | Read Vietnamese paperwork line by line | Clinician |
| `/ghi-chep-lam-sang/` | Ghi chép bệnh án AI | Clinician |
| `/thu-nghiem/` | Public demo hub | Anyone evaluating the product |

`/get-care/` and `/my-carepath/` are fully client-side: no fetch, no WebSocket,
no microphone.

## Language

Decided by audience, not globally — see
`docs/decisions/0023-foreign-patient-care-navigator.md`. Patient surfaces are
English; clinician surfaces are Vietnamese; clinician-facing elements keep their
Vietnamese even when embedded in an English screen, because the person acting on
a risk label is the clinician. Vietnamese copy is never deleted to make room for
English, and `scripts/check-diacritics.mjs` stays in force.

## Naming

The user must never need the English words “Scribe” or “Interpreter” to use
CarePath. They are internal terms for `scribe/carepath` and `interpreter/app`,
valid in code, comments and these documents, and never primary labels on a
user-facing screen.

Every clinical screen must say what is active, what it helps with, what to do
next, and its relevant limit or risk.

CarePath remains clinician-controlled: notes are drafts that require review, and
interpretation translates only. The module contracts are `ai-scribe.md` and
`live-interpreter.md`.

## What is prototype

The MVP ships some things as clearly-labelled prototypes, and the labels are
part of the contract:

- Provider results are curated sample data. CarePath has no live appointment
  availability and must never state any.
- The `/get-care/` visit and paperwork stages are scripted walkthroughs. They
  render the real gate components and the real `isGated` predicate over canned
  turns, and each says so on screen.
- Human escalation records a request and says plainly that no coordinator is on
  call.
