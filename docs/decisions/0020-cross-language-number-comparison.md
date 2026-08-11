# 0020 Cross-Language Number Comparison

Date: 2026-08-11

## Status

Accepted

## Context

`number_mismatch` compares the digits in the Vietnamese source against the
digits in the English translation and escalates the turn to **critical** when
they differ. The same comparison backs the eval's `number_exact` metric.

Both sides were read raw, but the two languages do not arrive in the same form:

- `normalize_text` converts Vietnamese number words to digits, so `ngày hai lần`
  becomes `ngày 2 lần`. Nothing does the equivalent for English, so `twice a
  day` stays a word.
- Vietnamese writes a decimal comma (`38,5`) where English writes a point
  (`38.5`), and `NUMBER_RE` only recognised the point.

So a correct translation looked like a dose discrepancy. `Uống 1 viên, ngày 2
lần` against `Take 1 tablet, twice a day` was **critical**. So was
`Paracetamol 500 mg ... 38,5 độ C` against `... 38.5 C`, and `tái khám sau ba
ngày` against `come back after three days`. Over-gating is the safe direction
for one turn, but at this rate the confirmation gate carries no signal, and a
clinician who dismisses it by habit is exactly how a real dose error passes.

Separately, `giọt` (drop) was missing from `NUMBER_FOLLOWERS` while every other
dose form was present. `nhỏ mắt một giọt` therefore never became `1 giọt`, the
dose regex never matched, and **eye and ear drop dosing was never detected as a
dose and never gated at all**. That is a recall gap, not a precision one.

## Decision

Fold spelled-out English counts (`one`…`twelve`, `once`, `twice`, `thrice`,
`half`) to digits and read a decimal comma as a decimal point before comparing
numbers. Apply it in `_numbers()` in the risk engine, which every caller routes
through, and in the eval's `canonical_numbers()`.

Only small counts are folded. Anything larger stays unmatched and is still
reported, so the change cannot mask a discrepancy it does not understand.

Add `giot` to `NUMBER_FOLLOWERS` in the shared normalizer.

Fix two further cross-language comparisons in the eval, which had the same
shape:

- `unit_exact` compared unit tokens directly, so `ống` against `ampoule` scored
  as a unit error. Units are now mapped to a canonical form
  (`viên`/`tablet` → TABLET, `ống`/`ampoule` → AMPOULE) before comparison.
- `negation_polarity` counted Vietnamese sentence-final `không`/`chưa`/`chứ` as
  negation. Those make a yes/no question, not a negative: `Anh có dị ứng thuốc
  nào không?` is `Do you have any drug allergy?`. A trailing particle is now
  stripped before counting; a mid-sentence `không` still counts.

## Consequences

- Correct translations stop being escalated. `Uống 1 viên, ngày 2 lần`,
  `38,5 độ C` and `tái khám sau ba ngày` no longer raise `number_mismatch`.
- Drop dosing is now detected and gated. `nhỏ mắt một giọt` produces a
  `dose_number` span where it previously produced none.
- Real discrepancies are unchanged: `500 mg` against `50 mg`, and `2 viên`
  against `three tablets`, both still classify **critical**.
- All 91 cases in `risk_cases.jsonl` pass **without edits**. The two changes
  cancel: drop doses now register, and the digit-versus-word mismatch that would
  have escalated them no longer fires. Zero misses on critical fixtures holds.
- Six cases added to `risk_precision_cases.jsonl` covering both directions,
  including a regression guard for the missing `giot`.
- The eval's published figures change because the measurement was wrong, not
  because the model improved. Re-scoring the same saved CKey run:
  `number_exact` 98% → **100%**, `unit_exact` 94% → **100%**,
  `negation_polarity` 90% → **98%**. `drug_name_exact` and `laterality_exact`
  were already 100% and are unaffected.
- `negation_polarity` and `unit_exact` are now quotable. They were excluded from
  the public site and the demo runbook while they were known-broken.

## Addendum: two further defects the corrected run exposed

Running the fixed metrics against real output surfaced three more problems of
the same shape. All are fixed and guarded.

1. `count_terms` counted **substrings**, so the negation cue `no` matched inside
   `noise`, `cannot`, `nothing` and `nodule`. "Hospital noise" scored as a
   negation error. Now matches whole words only.
2. `canonical_units` compared **multisets**, so "Eye drops 1 drop" — one
   instruction naming the form twice — failed against `1 giọt`. Units are now
   compared as a set: whether a form was preserved, dropped or swapped is the
   question, and the count belongs to the number metric.
3. English negation **contractions** were absent from `negation_cues.json`.
   `cannot`, `can't`, `don't`, `doesn't`, `won't`, `shouldn't`, `mustn't`,
   `isn't`, `aren't` and `didn't` are now cues. This was a recall gap in the
   engine, not only the metric: "Do not drink alcohol with this medicine" was
   the only phrasing that registered, and **"Don't take this with alcohol"
   registered no negation at all**. All 91 risk fixtures still pass unchanged;
   two precision cases guard it.

`parse_mt_output` also changed: a confidence outside [0, 1] — a model answering
`95` for 95% — no longer discards an otherwise valid translation. Confidence has
a safe default and the translation does not, so an unusable value becomes 0.0
and the turn takes the low-confidence path. This surfaced when a 50-row eval
died at row 49 on exactly that.
