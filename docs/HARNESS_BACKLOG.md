# Harness Backlog

Use this file when an agent discovers a missing harness capability but should
not change the operating model immediately.

## Template

```md
## Missing Harness Capability

### Title

Short name.

### Discovered While

Task or story that exposed the gap.

### Current Pain

What was hard, repeated, ambiguous, or unsafe?

### Suggested Improvement

What should be added or changed?

### Risk

Tiny, normal, or high-risk.

CLI value: `--risk tiny`, `--risk normal`, or `--risk high-risk`.

### Status

proposed | accepted | implemented | rejected
```

## Items

## Future Interpreter Risk-Lexicon Consolidation

### Discovered While

CP-RES-006 term-store consolidation.

### Current Pain

The Interpreter safety lexicons are also clinician-editable data, but they
govern deterministic risk classification rather than medical-term retrieval.

### Suggested Improvement

Evaluate a separate, clinician-approved consolidation only with a safety-fixture
and evaluation policy change. Do not merge them into the general term source.

### Risk

high-risk.

### Status

proposed
