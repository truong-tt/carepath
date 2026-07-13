# Overview

## Current Behavior

Scribe retrieval and Interpreter glossary seeding use separate authored term
files with different schemas.

## Target Behavior

One shared canonical term dataset generates both current serving artifacts.

## Affected Users

- Clinicians retain existing retrieval and Interpreter glossary behavior.
- Developers edit one source and regenerate deterministic artifacts.

## Non-Goals

- Merge Interpreter risk lexicons or alter risk-engine behavior.
