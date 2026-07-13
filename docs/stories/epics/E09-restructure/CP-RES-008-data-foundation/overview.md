# Overview

## Current Behavior

The GEC pipeline uses code profiles and unversioned dataset arguments; there is
no consent gate or frozen stratified evaluation fixture.

## Target Behavior

Versioned JSON run configs specify fixed seeds and dataset manifests. Training
stops before any model step unless the owner-approved manifest is complete. A
text-only frozen fixture reports every clinical safety category.

## Affected Users

- Training operators get reproducible runs and explicit governance failures.
- The owner retains sole authority to approve real clinical data.

## Non-Goals

- Source or collect clinical audio.
- Train a model or alter Scribe serving behavior.
