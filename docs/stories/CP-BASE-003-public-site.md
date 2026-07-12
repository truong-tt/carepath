# CP-BASE-003 Public CarePath Site

## Status

implemented

## Lane

normal

## Product Contract

The public site makes the two Vietnamese-first workflows distinct and remains
deployable with its diacritics, accessibility, browser, and Lighthouse gates.

## Relevant Product Docs

- `docs/product/carepath-suite.md`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `cd site; npm.cmd test` |
| E2E | `cd site; npx.cmd playwright test` |
| Platform | `npm.cmd run test:deploy-env`; `npm.cmd run build`; `npm.cmd run lighthouse` |

## Evidence

2026-07-12: lint passed; 45 unit tests and 5 deploy-environment tests passed;
the build and 7 browser tests passed; Lighthouse reported 100 performance,
100 accessibility, and 100 best practices.
