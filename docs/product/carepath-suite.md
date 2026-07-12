# CarePath Suite

CarePath is a Vietnamese-first clinical AI suite for Vietnamese clinics. It
has two distinct workflows; the user must never need to know the English terms
“Scribe” or “Interpreter” to choose the correct one.

| Workflow | Purpose | Primary action |
| --- | --- | --- |
| Ghi chép bệnh án AI | AI hears a consultation and prepares structured clinical notes. | Bắt đầu ghi chép |
| Phiên dịch khám bệnh trực tiếp | Translates between a Vietnamese-speaking clinician and an English-speaking patient during a consultation. | Bắt đầu phiên dịch |

The landing page frames this choice as `Bạn muốn hỗ trợ việc gì hôm nay?`.
Every clinical screen must say what workflow is active, what it helps with,
what to do next, and its relevant limit or risk.

CarePath remains clinician-controlled: Scribe drafts require review, and the
Interpreter translates only. The detailed module contracts are
`ai-scribe.md` and `live-interpreter.md`.
