# Visual QA Evidence

This directory contains versioned visual proof for CarePath’s public site and
interpreter experience. These images are documentation, not application assets.

## Coverage

- `site/` — landing and clinical-note workflow at desktop and mobile viewports.
- `interpreter/` — consent, quiz, device check, first-run, blocked-risk, and
  forced-colors states across desktop and mobile viewports.

## Retention

- Keep the complete evidence set in Git; it supports visual, accessibility, and
  responsive-regression review.
- Refresh a scenario only after its corresponding browser or visual QA changes.
- Name new captures by surface, state, and viewport, matching the existing
  convention (for example, `consent-checked-390x844.png`).
- Do not import images from this directory into runtime code or production
  bundles.
