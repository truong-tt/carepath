# CarePath Feature Intake

Every implementation request is classified before code changes. Record the
classification with `.\scripts\bin\harness-cli.exe intake`.

## Input Types

| Type | Use when | Typical artifact |
| --- | --- | --- |
| Change request | Bounded behavior, bug, copy, or UX refinement | Direct patch or story |
| New initiative | A new product area spanning multiple stories | Initiative note and stories |
| Maintenance request | Dependency, performance, delivery, or operational work | Story or decision |
| Harness improvement | Process, proof, template, or instruction work | Harness docs and trace |

## Lanes

### Tiny

Use for narrow docs, copy, or isolated maintenance with no safety, API, data,
or multi-module impact. Record intake, patch directly, and run the relevant
quick proof. A UX or product-flow change still updates
`docs/ux-redesign-carepath.md` first.

### Normal

Use for a bounded change to one product surface or shared implementation. Create
or update one story packet, define the validation, update proof flags, and
record a standard trace.

### High-Risk

Use `docs/templates/high-risk-story/` and record a durable decision when the
work changes safety behavior, architecture, data ownership, public API shape,
or validation policy. Ask the user before implementing when the direction is
ambiguous.

## CarePath Hard Gates

The following are always high-risk:

- Consent, microphone capture, raw-audio handling, retention, or privacy.
- Interpreter risk classification, confidence display, patient display, TTS,
  escalation, or fail-closed behavior.
- Medical advice boundaries, provider behavior, credentials, or external
  clinical data.
- Public API or WebSocket contract changes, database migrations, or changes
  that span the Scribe and Interpreter modules.
- Removing or weakening existing safety or validation requirements.

Use the existing test and eval fixtures whenever a risk-engine rule changes;
zero misses on critical fixtures remains a hard gate.
