# 0022 The Withheld Gap Is a Positional Invariant

Date: 2026-08-12

## Status

Accepted

## Context

CarePath withholds lines carrying a drug dose or a look-alike drug name until a
doctor confirms them. That withholding is the product, and it appears on three
separate surfaces: the landing hero document, the public demo hub
(`/thu-nghiem/`), and the live visit screen (`/kham-song-ngu/`).

Until now each surface signalled withholding differently. The demo hub tints the
row and adds a seal chip (`.d-row.is-gated`, `demo.css:323`). The visit screen
uses its own risk tiers. The landing hero does not signal it at all — all four
document rows resolve to English. The only thing the three shared was the colour
red.

Colour alone is a weak invariant. It is the first thing lost to a colour-vision
deficiency, to a monochrome print of a patient handout, to a low-brightness
phone in a bright consulting room, and to the eye of a doctor who has been on
shift for nine hours. A doctor who signs off on patient safety needs to be able
to answer *is anything being held back here?* by glancing, not by reading.

CP-UX-18 introduces a comparison spine — one vertical rule at a fixed grid
column, Vietnamese left, English right. That creates the opportunity to make the
answer structural rather than chromatic.

## Decision

**Withheld content occupies a fixed, consistent position: the right column of
the spine, left empty.**

The absence has a location. On every public surface, at every breakpoint, the
place where English appears is the same place, so the place where English is
*missing* is also the same place. A doctor scanning the right column sees the
gaps without reading a word.

Three rules follow and are binding on future work:

1. **Nothing stands in for the withheld content.** No placeholder text, no
   blurred or masked English, no skeleton bar sized to the missing string. The
   English is genuinely absent from the DOM. A short seal mark naming *why* the
   line is held is permitted and expected — that annotates the gap, it does not
   impersonate its contents — and it is what the demo hub already ships.
2. **The seal marks the edge of the gap, never its interior.** Seal vermilion
   keeps the single meaning `styles.css` assigns it. Filling the gap with a
   seal-tinted block would make withholding look like *content of a different
   kind* rather than like content that is not there.
3. **Below 40rem the spine rotates, and the gap rotates with it.** The two
   columns stack, so the gap becomes a full-width band at the position the
   English would have occupied. The reading — something belongs here and is not
   here — survives the rotation.
4. **The spine is drawn only where two registers exist.** Sections that carry a
   single statement per row — the refusals list, the limits block — use the
   margin column and one text column, and no rule. This is what makes the
   invariant readable: an empty right column can then only ever mean withheld,
   because a right column is only ever drawn when something belongs in it.

Colour is retained as a second, redundant channel. It is no longer the only one.

## Alternatives Considered

1. **Keep colour-only signalling and just restyle it.** Rejected: it leaves the
   invariant on the weakest available channel, and it was the status quo whose
   inconsistency across three surfaces prompted this.
2. **Fill the gap with masked or blurred English.** Rejected on safety grounds.
   The English must be absent from the DOM, not visually obscured; a masked
   string is still shipped to the patient's browser and is one CSS override or
   one screen reader away from being read out. It would also make the withheld
   line look denser than a confirmed one, which inverts the signal.
3. **A dedicated icon in the row gutter.** Rejected as insufficient alone: an
   icon is a mark to be read, at a size that competes with the type. It can
   supplement the gap; it cannot replace a positional invariant that works
   peripherally.
4. **A separate "held" panel listing withheld lines.** Rejected: it detaches the
   withholding from the line it applies to, so the doctor has to re-associate
   them. The gap must sit in the row it belongs to.

## Consequences

Positive:

- The withholding signal survives monochrome, colour-vision deficiency, low
  brightness, and peripheral vision.
- One visual grammar across landing, demo and visit. A doctor learns it once.
- The landing hero can now *perform* the withholding rather than describe it,
  which is the page's strongest available proof and costs one copy string.
- The safety property (English absent from the DOM) and the visual property (the
  column is empty) are the same property, so they cannot drift apart.

Tradeoffs:

- The spine's column position becomes load-bearing. Any future layout change to
  the right column is a safety-adjacent change, not a cosmetic one.
- Withheld rows are visually lighter than confirmed ones. This is correct — less
  content is present — but it inverts the usual convention where a warning state
  is heavier, and reviewers should expect it.
- The dark-mode spine rule needs its own token at higher luminance than
  `--p-rule`; if the rule fades, the gap loses the edge that defines it.

## Follow-Up

- An e2e assertion holds that gated English has zero DOM occurrences before the
  doctor-view toggle and appears after it. That assertion is the durable proof
  of this decision and must not be weakened.
- If the visit screen's risk tiers are ever restyled, they inherit rules 1–3.
