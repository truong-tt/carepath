# Validation

## Proof Strategy

Separate local repository proof from owner-only external proof. Local tests do
not establish a live deployment or authorize clinical data processing.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Scribe, Interpreter, shared, and training suites |
| Integration | Term-artifact drift, training baseline, mock Scribe smoke |
| E2E | Both Vite frontends' Playwright suites |
| Platform | Owner verifies Vercel and Space routes after configuration |
| Clinical | Owner supplies approved, de-identified rubric summary |

## Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest scribe\training\tests
cd interpreter; ..\.venv\Scripts\python.exe -m pytest
cd scribe\frontend; npm.cmd test; npm.cmd run test:deploy-env; npm.cmd run build; npm.cmd run e2e
cd interpreter\frontend; npm.cmd run lint; npm.cmd test; npm.cmd run build; npm.cmd run e2e
```

## Acceptance Evidence

2026-07-13 local proof passed: root Scribe suite 54; training 54 with one
optional skip; Interpreter 112 with one optional skip and a 50/50 safety eval;
Scribe frontend 45 unit, 5 deployment-environment, and 7 browser tests;
Interpreter console lint, 38 unit tests, build, and browser tests. Term
artifacts were current and the mock Scribe smoke passed.

2026-07-13 Vercel proof passed: the owner saved Root Directory as
`scribe/frontend`; production deployment `13b65c1` is Ready at
`https://carepath-omega.vercel.app`; and the live page presents both
Vietnamese-first module choices and their safety limits.

2026-07-13 public-priority proof passed: deployment `367aae7` is Ready at
`https://carepath-omega.vercel.app`. The live page makes **Ghi chép bệnh án
AI** the primary web action and labels **Phiên dịch khám bệnh trực tiếp** as
in development for the web, while retaining its translate-only safety limit.

2026-07-13 Hugging Face proof passed: authenticated owner access confirmed the
existing `tranth3truong/carepath-api` Docker Space and its documented runtime
secrets. The public build variable `VITE_PUBLIC_SITE_URL` was set to
`https://carepath-omega.vercel.app`; then a Space-only root commit `6538a14`
replaced the divergent older revision. The root commit omits non-runtime QA
images rejected by the Space Git receiver; GitHub retains those files.

The rebuilt Space is Running at
`https://tranth3truong-carepath-api.hf.space`. `GET /api/v1/health` returned
`asr_ready: true` and `llm_ready: true` with the configured CKey provider;
`GET /api/health` returned `provider_mode: mock`; and `/`,
`/ghi-chep-lam-sang/`, and `/phien-dich-y-khoa/` each returned HTTP 200. The
Interpreter product link returns to the canonical Vercel site with language
preserved.

2026-07-13 public availability update: Space commit `cc678b9` is Running.
`/phien-dich-y-khoa/`, its asset path, and `/console/` now return HTTP 404;
the Space root, `/ghi-chep-lam-sang/`, `/api/v1/health`, and `/api/health`
continue to return HTTP 200. The public Scribe site on Vercel also returns 200.

Pending owner evidence: the approved 50-note clinician-rating threshold
reached without storing clinical material in the repository. No container
provider is registered in Harness, so that clinical evidence cannot be
collected by this workspace.
