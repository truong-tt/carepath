# CP-UX-18 The Comparison Spine

## Status

implemented

## Lane

high-risk

## Product contract

The public surface is built out of the product's own mechanism rather than a
picture of its subject matter.

One vertical rule at a fixed grid column runs the landing page, the demo hub and
the visit screen. Vietnamese content sits left of it, English right of it, and
**withheld content is a gap in the right column at that same position** — so a
doctor learns one visual grammar for *not yet confirmed*, and a visitor sees the
withholding before any copy explains it.

Seal vermilion keeps its single meaning: it marks the edge of the gap, and it is
spent nowhere else.

Dark mode is a composed palette, not inherited token flips.

## Scope

- Spine grid tokens in `:root`; designed dark palette; `--shadow` removed.
- `landing.css` recomposed on the spine. The four `auto-fit` equal-cell grids —
  `.p-moments`, `.p-try`, `.p-steps`, `.p-refuse` — become registers.
- `.p-label` moves from a stacked eyebrow into the margin column.
- The zero-blur offset shadow on `.p-doc` is deleted.
- `.p-refuse li::before { content: "✕" }` becomes one authored inline SVG mark.
- `p-resolve` retargeted to travel rightward from the spine. It stays the only
  animation on the page.
- `demo.css`, `DemoHub.tsx`, `ConversationPanel.tsx`: the gated row renders as
  the positional gap. **Gating logic byte-identical** — still a conditional
  render, English still absent from the DOM.
- `visit.css` consumes the new tokens; no rule rewrites.
- One copy addition in `content/landing.ts`: a withheld marker on the hero
  document's last row, `Giữ lại — chờ bác sĩ xác nhận` /
  `Withheld — awaiting doctor confirmation`.
- **No change** to the risk engine, the confirmation gate, consent, microphone
  behaviour, TTS eligibility, or the WebSocket contract. No new dependency, no
  router, no state library, no CSS framework. No route path changes.

## Acceptance criteria

1. Vietnamese sits left of the spine and English right of it on `/`,
   `/thu-nghiem/` and `/kham-song-ngu/`, at the same grid column.
2. Withheld content renders as a gap in the right column at that position, and
   its English has zero DOM occurrences until the doctor view is opened.
3. No landing section uses an equal-cell `auto-fit` card grid.
4. No `.p-label` renders as a stacked eyebrow above a heading.
5. No zero-blur offset shadow remains in the public surface.
6. No Unicode glyph stands in for an icon.
7. Every token pair used together clears WCAG in both schemes — body ≥ 4.5:1,
   large ≥ 3:1 — with the computed table recorded in Evidence.
8. `:root` still resolves `--p-blue: #0f2e5c`, `--p-seal: #c41e22`,
   `--teal: #0f2e5c`, `--r-panel: 0`; body font contains `Be Vietnam Pro` and no
   Geist byte is requested on any route.
9. `h1` remains the largest `font-size` of every `h1/h2/h3`; `.p-hero` measures
   under 800px at 1440; no horizontal overflow at 320.
10. Zero running animations under `prefers-reduced-motion: reduce`.
11. axe reports no serious violations on `/` and `/thu-nghiem/`, light and dark.
12. Any heading leading change is re-measured with canvas
    `actualBoundingBoxAscent`/`Descent` on the real Vietnamese string. The
    measured floor is 1.172; headings hold 1.18.
13. Vietnamese text stays NFC-normalised with diacritics preserved.

## Validation

```powershell
npm.cmd --prefix scribe/frontend run lint
npm.cmd --prefix scribe/frontend test
npm.cmd --prefix scribe/frontend run build
npm.cmd --prefix scribe/frontend run e2e
npm.cmd --prefix scribe/frontend run build
node C:\Users\ADMIN\.claude\skills\impeccable\scripts\detect.mjs --json scribe/frontend/src
```

| Layer | Expected proof |
| --- | --- |
| Unit | Landing and demo component tests still pass; copy parity holds. |
| Integration | n/a — no backend surface changes. |
| E2E | Design-world tokens, `h1` largest, hero height budget, reduced motion, axe light and dark, gated English absent from the DOM before the toggle and present after. |
| Platform | Screenshots at 360, 390, 768, 1440 in both schemes. |
| Release | `npm run build` twice — the second run is the diacritics gate on the built output. |

## Decisions

- DEC-0022 — the withheld gap is a positional invariant.

## Harness Delta

None proposed. The existing lanes and templates covered this work.

## Evidence

2026-08-12, local. **Not deployed**, so platform proof is 0.

Lint clean. 79 unit tests. Production build twice, including the NFC diacritics
gate. 24 Playwright tests, all passing, including one new assertion:
*the hero withholds the dose lines rather than hiding them* — two `.p-held`
cells present, `take 1 tablet` and `fever is above` absent from the served HTML,
the non-dose line still resolving, and the gap's left edge measured at or right
of the Vietnamese cell's right edge.

**Contrast, computed not eyeballed.** 46 token pairs across both schemes, every
one clear. Two failures were found and fixed before any value shipped:

| Pair | Was | Now |
| --- | --- | --- |
| `--p-ink-faint` on `--p-paper-2` (light) | 4.07:1 — **below AA**, and had been since CP-UX-16 | 4.57:1 |
| `--p-spine-line` on `--p-paper-2` | n/a — the spine had no token | 3.02:1 light, 3.01:1 dark |

The spine holds 3:1 rather than the decorative hairline's 1.4:1 because it is a
meaningful graphic under WCAG 1.4.11: it is what gives the withheld gap an edge.

**Dark mode, composed.** Paper moved off blue-black (`#0b1017` → `#0e1116`) so
the committed field separates by hue as well as luminance, and `--p-field-edge`
draws the boundary the light scheme gets for free. The seal was pulled back from
`#ff6b64` (a consumer-alert coral) toward vermilion at `#ff7a6e`, which is as
dark as it can go while `.p-cta` still clears 4.5:1 painting `--p-paper` on it.

**Measured, not assumed.** `.p-hero` at 1440 was 866px against a 800px budget
after the first pass; merging the document's identity block into the hero's right
register and tightening row padding brought it to 760px, with content intact.
The `h1` fell from 5 rendered lines to 4 at 390px once a stale `grid-column`
line name — kept alive by source order after the register collapsed to one
column — was overridden at the narrow band.

**Seal discipline tightened.** Two seal-coloured left rules were spending the
page's one meaningful colour on things that are not withholding: `.p-limits`
("what we have not proven") and `.p-moments__note`. Both are gone. `.d-error` had
one too, on the argument that a red left rule means *withheld* — an error is not
a withholding, so it now carries a strong top rule instead. The seal marks the
edge of a gap and nothing else.

**Impeccable detector: 8 findings at CP-UX-17 → 3.** All three remaining are
`border-left: 3px` in `styles.css` (~644, ~1670, ~1874) on `.turn`,
`.hero-proof__stage > p` and `.sample-speaker` — orphaned rules from the
`ScribeShowcase.tsx` deleted in CP-UX-17, with zero references in any `.tsx`
or `.ts` file. They render nowhere. Deleting the dead rulesets is separate
scope and is filed as a tiny maintenance task rather than edited in place here.

**Screenshots.** `docs/qa-evidence/cp-ux-18-{light,dark}-{360,390,768,1440}-{landing,demo}.png`
— 16 captures. axe reports no serious or critical violations on `/` or
`/thu-nghiem/` at 390 and 1440, in both schemes.

The demo hub renders its degraded state in these captures because the Space runs
`PROVIDER_MODE=mock`; the gated-row layout is proved by the e2e suite, which
mocks the endpoint, rather than by the screenshots.

## Owner actions still required

1. Deploy — push to `origin/main`. Vercel builds from the push; the CLI does not
   work for this project.
