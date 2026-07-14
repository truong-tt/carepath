# CarePath Suite

CarePath is a Vietnamese-first clinical AI suite for Vietnamese clinics. It
has two distinct workflows; the user must never need to know the English terms
“Scribe” or “Interpreter” to choose the correct one.

| Workflow | Purpose | Primary action |
| --- | --- | --- |
| Ghi chép bệnh án AI | AI hears a consultation and prepares structured clinical notes. | Bắt đầu ghi chép |
| Phiên dịch khám bệnh trực tiếp | Translates between a Vietnamese-speaking clinician and an English-speaking patient during a consultation. | Đang phát triển — chưa thể truy cập |

The current public landing leads with the Scribe job to be done and keeps the
Interpreter visible as unavailable. Every clinical screen must say what
workflow is active, what it helps with, what to do next, and its relevant limit
or risk.

CarePath remains clinician-controlled: Scribe drafts require review, and the
Interpreter translates only. The detailed module contracts are
`ai-scribe.md` and `live-interpreter.md`.

The public web experience currently exposes Scribe as its only active product
journey. Interpreter remains visible as a non-interactive development status;
its browser routes stay closed until a separate release decision reopens them.
