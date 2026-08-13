# CarePath Documentation

Start every task with `AGENTS.md`. This index directs agents to the smallest
relevant context rather than every document in the repository.

## Current Product and Work

- `product/` — accepted contracts for CarePath, Ghi chép bệnh án AI, and Phiên
  dịch khám bệnh trực tiếp.
- `ux-redesign-carepath.md` — current UX implementation backlog; required
  before UX or product-flow implementation.
- `DEMO_RUNBOOK.md` — the pitch path, and what to say when questioned.
- `deploy.md` — Vercel and Hugging Face Space deployment. Read it before
  concluding a deploy is broken; the project names do not match the domain.

Two backlogs were removed on 2026-08-13 rather than left to mislead:
`onboarding-ux-fix-tasks.md` planned work on `interpreter/frontend/`, and
`../UI-FIX-PLAN.md` targeted the landing page's GSAP/bento build. That frontend
and every selector, file and route both documents named have since been
deleted. Their history is in Git.

## Harness: Read for Daily Work

- `HARNESS.md` — source hierarchy, task loop, and done definition.
- `FEATURE_INTAKE.md` — lane selection and CarePath hard gates.
- `ARCHITECTURE.md` — module and delivery boundaries.
- `CONTEXT_RULES.md` — minimum context by lane.
- `TEST_MATRIX.md` — behavior-to-proof baseline.
- `TRACE_SPEC.md` — durable completion evidence.
- `stories/`, `decisions/`, and `templates/` — selected work, settled
  tradeoffs, and new-work starters.

## Harness: Read Only When Triggered

- `TOOL_REGISTRY.md` — registering or using optional external tools.
- `HARNESS_AUDIT.md` — the `harness-cli audit` drift and entropy checks.
- `HARNESS_BACKLOG.md` and `IMPROVEMENT_PROTOCOL.md` — repeated Harness
  friction or process improvements.
- `GLOSSARY.md` — extending shared Harness terminology.

`HARNESS_COMPONENTS.md` and `HARNESS_MATURITY.md` were removed on 2026-08-13.
Both described the upstream `repository-harness` project — its roadmap, its
component taxonomy, and files such as `CONTRIBUTING.md` and `PHASE2.md` that
have never existed here. CarePath consumes the harness as a prebuilt binary
(DEC-0005), so neither document described anything in this repository.

## Evidence and History

- `qa-evidence/` — versioned visual QA proof and its retention index.
- `history/` — preserved MVP, demo-site, unification, and review documents.
  These are context only; do not reopen completed tickets as current work.
