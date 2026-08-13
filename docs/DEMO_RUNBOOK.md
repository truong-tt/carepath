# Demo runbook

One page. Everything measured, nothing assumed.

## Before you leave

Open the live site once and walk `/get-care/` to the end. That is the whole
check for the main path — it needs no build, no server and no keys.

```bash
cd scribe/frontend && npm run build
```

Run that too, so the local backstop is ready. **Always rebuild after
`npm run e2e`**: the e2e build points the bundle at `https://carepath-e2e.example`
and the served app silently breaks. This has cost an hour once already.

Only if you plan to show a **live** consultation at `/kham-song-ngu/` — confirm
the Vietnamese voice is staged at a **short** path:

```bash
ls models/vi-tts/espeak-ng-data
```

espeak-ng reads that directory with a native call that fails past the Windows
`MAX_PATH` limit, so the model cannot live in the HuggingFace cache. The
scripted pitch path never speaks, so this cannot break the four minutes.

## Run it

Use the deployed site: **https://carepath-medicaltranslation.vercel.app/**

Keep a local server open as the backstop, because a URL cannot load on a network
that is down:

```bash
cd scribe/frontend && npm run dev
```

The pitch path is `/get-care/`, and it makes **zero network requests** — no
fetch, no WebSocket, no microphone. `tests/journey.spec.ts` proves that by
aborting every request for the whole run and walking the journey end to end. So
the demo survives the venue wifi dying mid-pitch. What it cannot survive is the
wifi being down *before the page loads*, which is what the local server is for.

Nothing in the four minutes below needs the backend running.

## The four minutes

| Beat | What you do | What the judge sees |
|---|---|---|
| **Problem** | Open `/` and **wait two seconds before speaking** | A Vietnamese prescription at full size, two lines resolved into English and two marked `Withheld — line carries a dose`. Scroll once: the six-step journey, then 29.5% against 49.1% and Emma's clock |
| **Need** | `/get-care/` → **Use the example patient** → **Find care** | Five questions, no name, no passport, no date of birth. "CarePath does not diagnose" sits above the form |
| **Where** | Pick the dermatology clinic | Ranked on the words Emma used. The curated-data notice says availability is not live and never invented |
| **Prepare** | Scroll the visit brief | Her words on the left, the clinician's Vietnamese on the right — before she has had to explain anything |
| **Safety** | **Stop here.** Read the patient column aloud | `2 lines are waiting for the clinician`. The patient column shows `Held back — the clinician is checking this`. The dose is not on her screen. Then confirm both, and the English appears |
| **Paper** | Confirm the two dose lines | Four lines, two held until confirmed, then a sheet in English she can take home |
| **Follow-up** | **Save to My CarePath** | Medicines word-for-word as confirmed, documents in both languages, and a delete button |

The **Safety** beat is the pitch. Everything before it is setup and everything
after it is consequence, so do not rush it — let the judge notice the dose is
missing before you explain why.

The one sentence to land: **translation is not the safety mechanism,
verification is.** It is on screen at that beat.

Live paths, if asked to see the real thing: `/kham-song-ngu/` for a real
consultation and `/dich-giay-to/` for a real photographed document. Both need
the backend and both bill real time — one turn, not a whole visit.

## What to say when asked

**"Isn't this just Google Translate?"**
The confirm endpoint returns 409 from any state but `awaiting_confirm`. 91 risk
fixtures across 30 named failure modes, including cross-lingual number and
negation mismatch. A translator has no state machine and no clinician.

**"Did the AI decide that was dangerous?"**
No. The vision model only transcribes. Every line goes through the same rule
engine that guards spoken turns, so a look-alike drug name is caught by tested
code, not a model's judgement.

**"The demo is scripted — so is any of it real?"**
Say yes and be precise about which part. The turns are canned; the gate is not.
`/get-care/` renders `GateCard`, `TurnCard`, `DocumentReview` and `PatientSheet`
— the components a clinic uses — and what is withheld is decided by `isGated` in
`scribe/frontend/src/visit/types.ts`, the same predicate the server's statuses
feed in a real consultation. `scripted.test.ts` asserts the withholding against
those predicates rather than against itself, so if the safety rule changed, the
demo would stop demonstrating it and the test would fail. The scripting buys
determinism on venue wifi, not a different safety story. `/kham-song-ngu/` runs
the whole thing live if they want to see it.

**"What are your numbers?"**
A 50-case set through the live gateway: drug name, numbers, dose units and
laterality all **100%**. Negation polarity **98%**.

If asked about the missing 2%: one case, `Ngưng thuốc` → `Discontinue the
medication`. The negation is preserved; `discontinue` simply is not in our cue
list. We did not add it, because tuning the lexicon until the eval reads 100%
would make the eval measure nothing. That turn was gated for clinician
confirmation regardless — which is the actual point.

Report at `interpreter/eval/reports/ckey/`. Numbers move slightly run to run;
re-run before the pitch if you want the page to match exactly.

## If something breaks

On the scripted path — the four minutes above:

| Symptom | Do this |
|---|---|
| The venue wifi dies mid-pitch | Keep going. `/get-care/` made its last request when the page loaded |
| The site will not load at all | Switch to the laptop: `npm run dev`, then `http://localhost:5173/get-care/` |
| You lose your place, or want a second run | Open `/my-carepath/`, **Delete this episode**, and start again from `/get-care/` |
| A stage looks wrong after clicking back | The episode is in `sessionStorage`. Close the tab and reopen — that clears it |

On the live paths, if you chose to show them:

| Symptom | Do this |
|---|---|
| Microphone denied or mis-hears | Type instead. Every turn has a typed input beside the mic |
| A turn errors | Say it again. Turns are independent; nothing is lost |
| Page reloads mid-visit | It resumes. The visit id is in `sessionStorage` and the server replays the transcript |
| Document read fails | It adds nothing and says so. Move on to finishing the visit |
| Everything is slow | You are on `ckey`. Say the latency number out loud, or fall back to the scripted path |

## Showing the real AI path

Set `PROVIDER_MODE=ckey` and restart. Measured across 50 turns: **median 15s,
p90 54s, max 206s**. Do one turn, not a whole visit, and say the number out
loud — it is a gateway limit, not an architectural one.
