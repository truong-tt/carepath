# CarePath Test Matrix

This matrix maps the current CarePath baseline to proof. Status changes only
after the named evidence is actually run and recorded.

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CP-BASE-001 | Unified API and Ghi chép bệnh án AI remain available | yes | yes | no | no | implemented | 96 passed, 1 skipped; mock smoke passed (2026-07-12) |
| CP-BASE-002 | Interpreter remains translate-only and fail-closed | yes | yes | yes | no | implemented | Ruff; 109 passed, 1 skipped; mock eval 50/50; 4 browser tests passed (2026-07-12) |
| CP-BASE-003 | Public CarePath site remains Vietnamese-first and deployable | yes | no | yes | yes | implemented | 45 unit, 5 deploy-env, 7 browser tests; Lighthouse 100/100/100 (2026-07-12) |
| CP-BASE-004 | Interpreter console remains buildable and usable | yes | no | yes | no | implemented | lint; 38 unit; build; 4 browser tests passed (2026-07-12) |
| GEC-001 | Offline GEC training uses ViMedCSS and synthetic pairs without human-labeling tooling | no | yes | no | no | implemented | Ruff; 26 focused GEC tests; root 95 passed, 1 skipped (2026-07-12) |
| HARN-001 | Agent work follows durable CarePath intake and proof rules | no | yes | no | no | implemented | pinned merge install, CLI 0.1.11, init, matrix, audit, trace (2026-07-12) |

Proof labels mean the relevant layer has evidence for the baseline; they do not
claim every historical behavior was retested. Story packets define the exact
commands for future changes.
