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

Pending owner evidence: Vercel Root Directory set to `scribe/frontend`, Space
rebuilt from the root Dockerfile, documented live routes healthy, and the
approved 50-note clinician-rating threshold reached without storing clinical
material in the repository. No deployment or container provider is registered
in Harness, so those checks cannot be run by this workspace.
