# CP-UX-17 Public Demo Hub and One Design World

## Status

in-progress

## Lane

high-risk

## Product contract

The public site works, tells the truth, and can be tried.

`/api/*` is same-origin, so no CORS allow-list stands between the site and the
backend. `/thu-nghiem/` lets an anonymous visitor run three functions under
published limits: a Vietnamese prescription photo, a discharge summary, and a
two-way consultation. Every figure on the landing page carries its source, and
the competitive argument is time and coverage rather than price.

One token system — the document world — serves the landing and both tools.

## Scope

- Same-origin `/api/*` rewrite; relax `validate-deploy-env` to accept an empty
  `VITE_API_BASE`.
- Vercel functions at `/api/demo/*` for quota, size caps, and provider mode.
  They proxy the existing FastAPI; they do not implement OCR or translation.
- Per-request `PROVIDER_MODE=demo` override on the document route.
- New route `/thu-nghiem/` (pathname check, no router).
- Promote `--p-*` from `.landing` to `:root`; retheme `visit.css` and the Scribe
  tool onto it; delete Geist; narrow the font preload to two faces.
- Correct three figures in `src/content/landing.ts`, credit Divi 2007, rebuild
  the price section as time-and-coverage.
- New landing sections `Thời điểm nguy hiểm` and `Thử ngay`.
- Metadata, canonical, `og:image`, sitemap, robots for the new domain.
- Delete `ScribeShowcase.tsx` (unreachable) and dead `styles.css` blocks.
- **No change** to gate logic, risk rules, TTS eligibility, consent, microphone
  behaviour, or the WebSocket contract. No router, state library, or i18n
  dependency.

## Acceptance criteria

1. `/api/v1/health` returns `200` from the new domain with no `Origin`
   allow-list involved; `/kham-song-ngu/` and `/ghi-chep-lam-sang/` work in
   production.
2. `22,8 triệu` → `21,2 triệu`; `83.500–100.000 người nước ngoài` → `161.992 lao
   động nước ngoài`; the `25–100 USD mỗi trang` claim is absent.
3. The 29,5% / 49,1% comparison cites Divi et al., Int J Qual Health Care 19(2),
   2007.
4. `--p-blue` resolves on `document.documentElement`; no Geist face is requested
   on any route; no `preloaded but not used` warning.
5. All three demo panels run for an anonymous visitor, and the limits are visible
   before the first run.
6. A demo response body never contains a high-risk line, only its gated
   placeholder.
7. Quota exhaustion returns `429` with `Retry-After` and Vietnamese copy.
8. `h1` leading no longer collides Vietnamese stacked diacritics.
9. axe reports no serious violations on `/` and `/thu-nghiem/`, light and dark.
10. Existing visit-screen e2e passes unchanged.

## Validation

```powershell
npm.cmd --prefix scribe/frontend run lint
npm.cmd --prefix scribe/frontend test
npm.cmd --prefix scribe/frontend run test:deploy-env
npm.cmd --prefix scribe/frontend run build
npm.cmd --prefix scribe/frontend run e2e
npm.cmd --prefix scribe/frontend run build
python -m pytest
python scripts/smoke_backend.py
python scripts/build_term_artifacts.py --check
```

## Decisions

- DEC-0021 — same-origin API and a proxied public demo.

## Evidence

2026-08-12, local. **Not deployed**, so platform proof is 0.

Frontend: lint clean; 79 unit tests; 10 deployment-environment tests; production
build and the NFC diacritics gate; 22 Playwright tests. New coverage: the gated
line hides its English until the doctor view is opened; a scripted sample is
labelled as one; quota exhaustion returns 429 and renders no result; an
unreadable document is reported and never replaced with the sample; the hub
degrades honestly for `demo`, `mock` and unreachable backends; axe clean in
light and dark; all three routes render in one design world with no Geist byte
requested; the served title and OG metadata survive hydration.

Backend: root pytest 107 passed 1 skipped; interpreter 186 passed 1 skipped;
shared 52; mock smoke; term-drift check current; safety eval 1.0 on all five
preservation metrics.

Live diagnosis recorded in DEC-0021: the production 400 was a stale
`CORS_ORIGINS` allow-list after the domain move, not downtime — the Space
answers 200 when sent the old Origin. The WebSocket was verified to connect
cross-origin from the new domain, so `/ws/*` stays direct.

Measured, not assumed: `line-height: 0.94` on the Vietnamese `h1` overlapped
`ệ` against the next line's `ấ` by 8.9px in Be Vietnam Pro 800. The clearance
floor is 1.172, so 1.18 shipped.

Impeccable detector: 8 findings reduced to 6. The three remaining seal
left-rules are deliberate product vocabulary for withheld content; the other
three are pre-existing in the tool stylesheets.

## Owner actions still required

1. Deploy. The CORS fix is code-only, so the live site stays broken until then.
2. Set the Space to `PROVIDER_MODE=ckey` with `LLM_API_KEY` if own-upload should
   read real documents. It currently runs `mock`, so the hub correctly shows
   **Bản thử đang tạm dừng** rather than inventing output.
3. Set `DEMO_API_BASE` on Vercel, and `VITE_WS_BASE` to the Space origin with
   `VITE_API_BASE` empty.
