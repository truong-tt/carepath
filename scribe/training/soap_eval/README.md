# SOAP Note Clinical Rating Protocol

This Scribe-only quality track contains only the anonymous rating schema. Do not put audio,
transcripts, patient identifiers, or SOAP note text in this repository.

## Owner prerequisites

Before creating the real rating export, the owner must have a pilot-clinic
agreement, documented consent or other lawful basis, de-identification process,
and an approved secure review environment. The clinical source material stays
there; this repository is not that environment.

## Rubric

Rate each generated note using an anonymous `note_id` only.

| Field | Range | Meaning |
| --- | --- | --- |
| `completeness` | 1–5 | 1 = clinically important content missing; 5 = all material consultation details represented. |
| `hallucination` | 0–3 | 0 = none; 1 = minor unsupported wording; 2 = clinically relevant unsupported content; 3 = potentially harmful unsupported content. |
| `terminology` | 1–5 | 1 = dangerous/inaccurate term use; 5 = clinically accurate terminology. |
| `status` | `accepted`, `needs_correction`, `unsafe` | Clinician's final disposition. |

`clinician_id` is an approved pseudonymous reviewer identifier. `reviewed_at`
uses ISO 8601 date/time. At least 50 distinct notes must be rated before a
fine-tuning decision. The validator reports readiness to **decide**, never
approval to fine-tune.

## Run

Export ratings without clinical source text to an approved local path, then run:

```powershell
python scribe/training/scripts/validate_soap_ratings.py --input C:\approved\soap-ratings.csv
```

Review the resulting summary with the clinical owner. Any hallucination score
of 2 or 3, or any `unsafe` disposition, requires documented investigation
before deciding whether training, retrieval, or prompting should change.
