# 0010 Shared Normalization Contract

Date: 2026-07-13

## Status

Accepted

## Context

Interpreter, Scribe scoring, training scoring, and both lexical retrievers
carried local normalization implementations. Their names overlapped, but their
contracts differed: the Interpreter normalizes units, Vietnamese number words,
and relative dates; scoring compares case-insensitively without semantic
conversion; lexical retrieval additionally folds diacritics and punctuation.

## Decision

Create the installable `shared/carepath_shared` package. Move the Interpreter
normalizer there unchanged as `normalize_text`, and make every former local
normalizer a direct import from this package. Keep the existing scoring and
retrieval semantics as the separately named `normalize_for_metrics` and
`normalize_for_match` functions, rather than silently changing metric scores or
term matching.

## Consequences

- Normalization algorithms have one owner and one characterization suite.
- Existing module import paths remain compatible.
- A future semantic consolidation must explicitly revise the characterization
  suite and evaluation baseline; it is not part of this restructure.
