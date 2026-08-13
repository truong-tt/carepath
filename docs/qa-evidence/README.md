# Visual QA Evidence

Versioned visual proof for CarePath's public surface. These images are
documentation, not application assets.

## Coverage

Captures are named for the story that produced them, so each set is evidence
for a specific accepted change rather than a rolling snapshot of "the site":

- `cp-ux-18-*` — the comparison-spine visual system, landing and demo hub,
  light and dark, at 360 / 390 / 768 / 1440.
- `cp-ux-19-*` — the paperwork route, same schemes and viewports.

Screenshots are written by the Playwright suite in `scribe/frontend/tests/`.
Rebuild them by running `npm run e2e` from `scribe/frontend/`.

## Retention

- Keep the set in Git; it supports visual, accessibility, and
  responsive-regression review.
- Refresh a scenario only after its corresponding browser or visual QA changes.
- Name new captures for their story, surface, scheme and viewport, matching the
  existing convention (for example, `cp-ux-19-light-390-paperwork.png`).
- Do not import images from this directory into runtime code or production
  bundles.
- **Delete a set when its surface is deleted.** Two were removed on 2026-08-13:
  `interpreter/` (38 captures of the consent, quiz, device-check and console
  screens, a frontend deleted when the bilingual visit replaced it) and `site/`
  (8 captures of a landing page redesigned twice since). Evidence for a screen
  that no longer exists is not proof of anything, and Git keeps the history.
