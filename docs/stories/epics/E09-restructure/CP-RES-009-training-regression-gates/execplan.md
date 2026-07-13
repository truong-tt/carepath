# Exec Plan

## Goal

Make GEC evaluation reviewable and prevent safety-category regressions from
reaching the serving-bundle export step.

## Work Phases

1. Add exact-match reporting and generate the versioned frozen baseline.
2. Extend the gate with drug-name and dosage checks.
3. Run the frozen fixture through the real pipeline evaluation path before
   export.
4. Add CPU-only CI report and export-smoke proof.

## Hard Gates

- The fixture hash must match its manifest.
- A candidate cannot regress drug-name recall or dosage number/unit
  preservation relative to raw ASR.
- The export path remains GPU-free in CI through the injected generator only.
