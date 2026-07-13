# SOAP Note In-House Review Protocol

This Scribe-only quality track contains only the anonymous rating schema. Do not put audio,
transcripts, patient identifiers, or SOAP note text in this repository.

## Current scope

This tool supports informational in-house testing only. Use synthetic or
already-approved de-identified material outside the repository. Do not put
source audio, transcripts, patient identifiers, or SOAP note text here.

The summary does not create a release target or authorize fine-tuning,
provider, or safety-policy changes. Those changes require a separate owner
decision.

## Rubric

Rate each generated note using an anonymous `note_id` only.

| Field | Range | Meaning |
| --- | --- | --- |
| `completeness` | 1–5 | 1 = clinically important content missing; 5 = all material consultation details represented. |
| `hallucination` | 0–3 | 0 = none; 1 = minor unsupported wording; 2 = clinically relevant unsupported content; 3 = potentially harmful unsupported content. |
| `terminology` | 1–5 | 1 = dangerous/inaccurate term use; 5 = clinically accurate terminology. |
| `status` | `accepted`, `needs_correction`, `unsafe` | Clinician's final disposition. |

`clinician_id` is an approved pseudonymous reviewer identifier. `reviewed_at`
uses ISO 8601 date/time. There is no minimum sample-size target. The validator
reports quality signals only; it never reports readiness or approval to change
the model.

## Run

Export ratings without clinical source text to an approved local path, then run:

```powershell
python scribe/training/scripts/validate_soap_ratings.py --input C:\approved\soap-ratings.csv
```

Review the resulting summary with the designated in-house reviewer. Any
hallucination score of 2 or 3, or any `unsafe` disposition, requires documented
investigation and retention of the current model behavior unless a separate
owner decision authorizes a change.
