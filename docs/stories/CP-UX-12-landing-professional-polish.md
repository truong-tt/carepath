# CP-UX-12 Professional Landing Polish

## Status

implemented

## Lane

normal

## Product contract

The public landing keeps the CP-UX-11 problem-led structure and copy contract,
and presents it with professional polish: the hero shows a conversation-to-draft
proof of the product, the Interpreter development status is visible but quiet,
the page has one dark closing moment instead of three, and the footer stays
readable at phone widths.

## Scope

- Replace the hero daily-flow table with a static conversation-to-draft proof
  panel reusing the sanitized sample; Subjective and Objective rows only.
- Keep both hero actions on one row at desktop widths.
- Restyle the Interpreter status as a bordered notice; same element, same
  strings, still non-interactive.
- One shared section-padding rhythm; trust section light; start section is the
  only dark section before the footer.
- Root-cause the footer responsive bug (late `.site-footer` override) and stack
  the footer at phone widths.

No route, API, form, showcase-interaction, Scribe-tool, consent, audio,
Interpreter, or safety behavior changes. No new dependency.

## Acceptance criteria

- Hero shows the proof panel labeled as a cleaned sample; `Chờ bác sĩ nhập
  hoặc xác nhận.` still never renders before the doctor opens the draft step.
- Both hero actions render on one row at 1024 px and wider.
- Interpreter status keeps exact strings, zero links or buttons, and loses the
  dark band treatment.
- Exactly one dark section between the evidence grid and the footer.
- Footer stacks into readable rows at 320, 360, and 390 px.
- Hero under 800 px at 1440×900; H1 line limits hold; no horizontal overflow
  from 320 to 1440 px.
- Lint, unit, deploy-env, build with diacritics gate, Playwright, Lighthouse,
  and combined-app checks pass.

## Validation

```powershell
cd scribe\frontend
npm.cmd run lint
npm.cmd test
npm.cmd run test:deploy-env
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
cd ..\..
python -m pytest scribe/tests/test_combined_app.py
```

## Evidence

2026-07-15: lint passed; 46 unit tests passed; 5 deploy-env tests passed;
production build and NFC diacritics gate passed; 8 Playwright tests passed
(keyboard, responsive 320–1440, axe light and dark, touch menu, reduced
motion); combined-app 3 passed; Lighthouse 100/100/100 with CLS 0.
Desktop and mobile screenshots verified: hero proof panel above the fold,
single-row hero actions, quiet Interpreter notice, one dark closing section,
stacked phone footer.
