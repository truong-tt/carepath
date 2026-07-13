# Overview

## Current Behavior

Normalization logic is duplicated across the Interpreter, Scribe evaluation,
GEC training metrics, and both lexical retrievers.

## Target Behavior

`shared/carepath_shared/normalize.py` owns all normalization algorithms;
existing module paths remain import-compatible through direct re-exports.

## Affected Users

- Clinicians receive unchanged Interpreter safety normalization.
- Developers and training operators use one implementation owner.

## Non-Goals

- Change scoring, retrieval, routes, or safety policy.
