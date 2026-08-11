# Demo runbook

One page. Everything measured, nothing assumed.

## Before you leave

```bash
cd scribe/frontend && npm run build
```

**Always rebuild after `npm run e2e`.** The e2e build points the bundle at
`https://carepath-e2e.example` and the served app silently breaks. This has cost
an hour once already.

Confirm the Vietnamese voice is staged at a **short** path:

```bash
ls models/vi-tts/espeak-ng-data
```

espeak-ng reads that directory with a native call that fails past the Windows
`MAX_PATH` limit, so the model cannot live in the HuggingFace cache.

## Run it

```bash
uvicorn carepath.main:app --app-dir scribe --port 8000
```

`.env` is already set to `PROVIDER_MODE=demo`. Open **Chrome** at
`http://127.0.0.1:8000/kham-song-ngu/`.

Demo mode is scripted and makes **zero outbound network calls** — verified by
running the whole flow with the socket connect path poisoned. The venue wifi
cannot break the demo.

## The four minutes

| Beat | What you do | What the judge sees |
|---|---|---|
| **Problem** | Open `/` first and **wait two seconds before speaking** | A Vietnamese prescription at full size, then the English resolving under each line. Scroll once: 29,5% against 49,1%, the three highest-risk moments, the two priced incumbents |
| **Start** | Age 34, nam, "nổi mẩn da" | One screen, no login, no settings |
| **Conversation** | Type or speak the scripted lines | English in, Vietnamese out, entity chips appearing |
| **Safety** | *"I take 15 milligrams"* | Red gate, 42% confidence, back-translation. **The patient pane shows nothing.** Click **Sửa**, correct to 500 mg, confirm |
| **Paper** | Photograph the prescription | Four lines read, each with drug / dose / frequency chips, all gated |
| **Finish** | Kết thúc và tạo hồ sơ | Vietnamese record, English patient packet, medication list |

Scripted lines are in `interpreter/app/providers/demo_scenario.json`. Anything
off-script falls back to a visible `[en->vi] …` placeholder rather than failing.

The landing page's opening animation is the whole pitch in two seconds — let it
finish before you talk over it. It also sets up the **Paper** beat: the judge
has already seen the object you are about to photograph.

## What to say when asked

**"Isn't this just Google Translate?"**
The confirm endpoint returns 409 from any state but `awaiting_confirm`. 91 risk
fixtures across 30 named failure modes, including cross-lingual number and
negation mismatch. A translator has no state machine and no clinician.

**"Did the AI decide that was dangerous?"**
No. The vision model only transcribes. Every line goes through the same rule
engine that guards spoken turns, so a look-alike drug name is caught by tested
code, not a model's judgement.

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

| Symptom | Do this |
|---|---|
| Microphone denied or mis-hears | Type instead. Every turn has a typed input beside the mic |
| A turn errors | Say it again. Turns are independent; nothing is lost |
| Page reloads mid-visit | It resumes. The visit id is in `sessionStorage` and the server replays the transcript |
| Document read fails | It adds nothing and says so. Move on to finishing the visit |
| Everything is slow | You are on `ckey`. Set `PROVIDER_MODE=demo` and restart |

## Showing the real AI path

Set `PROVIDER_MODE=ckey` and restart. Measured across 50 turns: **median 15s,
p90 54s, max 206s**. Do one turn, not a whole visit, and say the number out
loud — it is a gateway limit, not an architectural one.
