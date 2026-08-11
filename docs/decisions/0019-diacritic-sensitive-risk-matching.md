# 0019 Diacritic-Sensitive Risk Matching

Date: 2026-08-11

## Status

Accepted

## Context

The risk engine matched every lexicon term against diacritic-folded text, so
that undiacritized ASR output ("toi bi di ung") would still reach the allergy
gate. Folding is lossy in Vietnamese, and unrelated words collapse onto the
same string:

- `nhỏ tai` (ear drops, a route cue) and the `nhớ tái` in `nhớ tái khám`
  (remember to come back) both fold to `nho tai`.
- `nhẹ` (mild, a critical symptom-severity cue) and `nhé` (a friendly
  sentence-final particle) both fold to `nhe`.

Ordinary clinical courtesy therefore produced high and even critical risk
tiers. `Nhớ tái khám nhé` classified as **critical**, gating a benign sentence
behind clinician confirmation. Over-gating is the safe direction for a single
turn, but at this rate the confirmation gate carries no signal: it fires on
almost everything, so a clinician learns to dismiss it, which is exactly how a
real dose error gets waved through.

The existing 91-case fixture suite could not detect this. It asserts
`expected_kinds <= produced_kinds`, a subset check, so it constrains recall
only and is structurally blind to false positives.

## Decision

Match diacritic-sensitively first. Fall back to folded matching only where the
matched region of the original text carries no diacritics of its own.

The check is applied per matched region rather than per turn, so text that lost
tone marks on only some words still matches on those words. `Tôi bị di ung
penicillin` continues to reach the allergy gate.

Word-anchor multi-word terms as well as single-word terms; previously only
single-word terms were anchored and multi-word terms used an unanchored
substring search.

Add `interpreter/eval/fixtures/risk_precision_cases.jsonl` and
`test_risk_precision_cases`, a second fixture set carrying `max_tier` and
`forbidden_kinds` so false positives are assertable. It is kept separate from
`risk_cases.jsonl` so the 30-failure-mode coverage contract there is untouched.

## Consequences

- Benign Vietnamese no longer gates. `Nhớ tái khám nhé` is `low`, not
  `critical`; `Cảm ơn bác sĩ` is `medium`, not gated.
- Recall on undiacritized and partially diacritized ASR text is preserved, and
  is now asserted rather than assumed.
- All 91 risk fixtures, the 6 risk engine tests, and the 50-row mock safety
  eval pass unchanged. Zero misses on critical fixtures still holds.
- False positives are now a testable property of the engine. Any future
  matching change that reintroduces a folding collision fails
  `test_risk_precision_cases`; the guard was verified by mutation, confirming
  it fails when the fix is reverted.
- Not addressed, and still open: `uống` (to take orally) is a route cue that
  fires on any sentence about drinking, so `Tôi uống nước` is `high`; and
  Vietnamese number words normalize to digits while English number words do
  not, so `sau ba ngày` against `after three days` raises a false
  `number_mismatch`. Both are lexicon and normalization concerns rather than
  matching concerns, and are left for a separate decision.
