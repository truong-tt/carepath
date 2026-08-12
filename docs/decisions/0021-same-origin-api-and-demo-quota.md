# 0021 Same-Origin API and a Proxied Public Demo

Date: 2026-08-12

## Status

Accepted

## Context

Two problems arrived together, and the obvious fix for each is wrong.

**The public site's API calls fail.** Moving the site from
`carepath-omega.vercel.app` to `carepath-medicaltranslation.vercel.app` broke
every request. The backend is healthy — `/api/v1/health` on the Space returns
`200` with `llm_provider: ckey`, `asr_ready: true`, `llm_ready: true` — but its
`CORS_ORIGINS` still names only the old host, so `_reject_disallowed_origin`
(`scribe/carepath/main.py:123-128`) answers `400 Disallowed CORS origin`. Both
tool routes render **Mất kết nối máy chủ** in production.

The obvious fix is to add the new host to `CORS_ORIGINS`. That restores service
and leaves the mechanism intact: the site's origin is coupled to a backend
environment variable, and the coupling is invisible until a deploy silently
breaks. `vercel.json` has no `/api/*` rewrite, so every call is cross-origin by
construction and every future domain, preview URL, or custom domain re-enters the
same failure.

**The public site has no working demo.** The `h1` promises CarePath reads
Vietnamese paperwork; the prescription in the hero is a hardcoded string. A real
OCR endpoint exists (`POST /api/v1/visits/{id}/documents`) and the landing never
calls it. Opening it to anonymous visitors needs quota, size caps, and a provider
mode that does not bill the `ckey` account.

The obvious fix is a Vercel serverless function that does the demo work — read
the image, translate the lines, return them. That is the dangerous one. The risk
engine, glossary, normalizer and confirmation gate live in the FastAPI. A second
implementation would produce patient-visible output that never passes them,
which fails safety invariants 2 (high-risk turns blocked until the doctor
confirms) and 6 (fail closed) in `AGENTS.md`, and is a hard gate under
`docs/FEATURE_INTAKE.md`.

## Decision

**Make the API same-origin.** `vercel.json` rewrites `/api/:path*` to the Space.
The browser sends no cross-origin request, so no `Origin` allow-list participates
and no domain change can break the API again. `VITE_API_BASE` becomes empty on
the Vercel build; `scripts/validate-deploy-env.mjs` is relaxed to accept an empty
value alongside a valid HTTPS origin, having previously hard-failed on it.

`CORS_ORIGINS` stays configured for local development and for any surface that
genuinely is cross-origin, but it stops being load-bearing for production.

**The demo proxies; it does not re-implement.** Vercel functions under
`/api/demo/*` own only what the FastAPI should not: per-IP quota, request size
caps, and selecting the provider mode. They forward to the same endpoints the
product uses. The FastAPI remains the single AI path and the single gate.

```
browser → /api/demo/*        Vercel function: quota, size caps, mode header
             ↓
        FastAPI (Space)      PROVIDER_MODE=demo for public traffic
             ↓
        normalizer → glossary → risk engine → confirmation gate
```

**Public traffic runs `PROVIDER_MODE=demo`.** That mode already replaces MT and
the reviewer with canned maps while the normalizer, glossary, risk engine,
confirmation flow and persistence all still run for real
(`interpreter/app/providers/registry.py:100-110`). So the demo is instant, costs
nothing per run, and the safety behaviour on display is genuine rather than
staged. The `ckey` path stays reachable behind `X-Team-Code` for pilot clinics.

Demo limits, stated in the UI rather than a footer: 5 runs per IP per day, one
image up to 4 MB or 600 characters of text, samples provided, nothing persisted,
and `Kết quả demo — không dùng cho lâm sàng` on every output.

## Consequences

- The production outage is fixed by routing, not by an allow-list entry. Preview
  deployments and any future domain work without backend configuration.
- The API host stops being public: `DEMO_API_BASE` is server-side, so the Space
  URL is no longer readable from the client bundle. The `VITE_API_BASE` value in
  today's bundle is.
- There remains exactly one implementation of translation and risk classification.
  A demo response can contain a gated placeholder but never the gated content —
  asserted by test, because "the proxy forwards faithfully" is the kind of claim
  that stops being true during a refactor.
- Vercel rewrites may not carry a WebSocket upgrade. If they do not, `/ws/*`
  keeps `VITE_API_BASE` cross-origin and `CORS_ORIGINS` gains the new domain for
  that path only — a narrower version of the coupling, not its removal. Verified
  before the demo hub is built on it.
- Quota is in-memory per function instance, so it is approximate under scale-out.
  That is acceptable: the backstop is `PROVIDER_MODE=demo`, which makes the worst
  case wasted CPU rather than spend. Vercel KV is the upgrade if abuse appears.
- The Space's cold start (20–40s) becomes visible to anonymous visitors. The demo
  must show a real wake-up state; the fake progress timer in
  `ScribeTool.tsx:176-179` — two `setTimeout` calls unrelated to actual progress
  — must not be reused for it.
