# CarePath Scribe research pack

This directory turns the literature review into testable CarePath hypotheses. It is
not a bibliography-only archive and it is not production evidence. The tracked
manifest records the exact paper versions and SHA-256 hashes; downloaded PDFs live
in ignored `papers/` so Git does not carry third-party binaries.

## Reproduce the snapshot

From the repository root:

```powershell
python scribe/research/download_papers.py
python scribe/research/download_papers.py --check
```

The default command downloads only missing PDFs. Existing or newly downloaded files
must match `papers.json`; a changed upstream file fails closed instead of silently
updating the research record. Delete a suspect local PDF only after reviewing the
new publisher version and intentionally updating its manifest URL, analysis, and
hash.

`papers.json` is the source of truth for the per-paper research question, dataset,
method, strongest result, limitations, publication status, paper license, CarePath
hypothesis, and planned experiment. Paper licenses do **not** grant rights to the
underlying datasets, models, YouTube audio, dictionaries, transcripts, or patient
content.

## Evidence-to-design matrix

| Evidence | What it teaches us | CarePath experiment | Decision gate |
| --- | --- | --- | --- |
| ViMedCSS | Overall Vietnamese WER and English medical-term accuracy move differently. | Benchmark Gipformer and direct ASR LoRA on test/hard with WER, CS-WER/PIER, term recall, number/unit accuracy, latency, and VRAM. | Select no candidate that improves aggregate WER while regressing critical terms or numbers. |
| LLM-generated near misses | Contrastive negatives near true code-switch points improve Whisper LoRA beyond ordinary fine-tuning. | Run only after plain LoRA clears a 5% relative WER and CS-WER improvement; require genuine beam hypotheses and acoustic, phonemic, and textual filters. | Near-miss variant must beat plain LoRA on both hard-split WER and PIER without a safety regression. |
| DARAG | Synthetic errors improve GEC generalization; retrieved named entities help novel terms. | Compare Gipformer alone, GEC from real Gipformer error pairs plus lexical retrieval, and that GEC with text-only phonetic augmentation. | At least 5% relative improvement in hard PIER or medical-term error; clean WER may worsen by no more than one absolute point. |
| PiDA | Vietnamese substitutions are mainly phonetic; text corruption can improve noisy-input robustness without TTS. | Mix clean and vowel/tone/consonant/code-switch corruptions 1:1 for the GEC candidate. | Continue to costly TTS only if text-only augmentation produces a safe held-out gain. |
| VietMed | Accent, disease group, recording condition, and speaker-role diversity reveal domain failures. | Keep an untouched out-of-domain evaluation set and report available slices. | A candidate cannot win on ViMedCSS while materially regressing VietMed medical-term or number accuracy. |
| MedEV | A large bilingual medical lexicon is useful for terminology alignment, not dialogue-to-note supervision. | Cross-check silver Vietnamese terminology against MedEV and CarePath's canonical term store. | Never train SOAP generation directly from parallel translation sentences. |
| SpecialtyScribe | Extract, ground/retrieve, then write; smaller specialized components can compete with larger models. | Reuse one Qwen base and one adapter for two passes: typed facts with source spans, then grounded SOAP JSON. | Every critical generated fact must resolve to extracted transcript evidence. |
| Multi-stage medical summarization | Entity and affirmation extraction before generation improves medical correctness over one-shot prompting. | Preserve negation and uncertainty in the fact pass and block unsupported medication, dose, diagnosis, number, or negation. | Any unsupported critical fact blocks export. |
| MTS-Dialog | Public short dialogue/note pairs support section generation and fact-based error analysis. | Translate/adapt training examples with deterministic teacher settings and provenance; reject alignment failures. | Silver data is research-only and never counts as Vietnamese clinical validation. |
| ACI-BENCH | Full encounters expose long-context omissions and SOAP-structure problems absent from short snippets. | Adapt training examples only; reserve validation/test for section completeness and factual tests. | No split leakage; valid schema and omission performance must be non-inferior to the current CKey baseline. |
| Medical-note evaluation | ROUGE and other metrics vary by dataset; facts, hallucinations, and omissions need explicit measurement. | Compare CKey, base Qwen, and adapter with factual F1, omissions, hallucinations, negation, medications, doses, and numbers. | ROUGE is diagnostic only; factual safety gates control export. |
| Feedback-derived checklists | Interpretable checklists derived from real failures align better with clinician preferences than generic metrics. | Build deterministic Vietnamese checklist items from CarePath's frozen failure categories; LLM grading remains triage evidence. | Owner review informs usability only and cannot promote a research model to production. |

## Ranked research sequence

1. **Direct Vietnamese medical ASR adaptation.** Establish frozen Gipformer,
   PhoWhisper/Whisper LoRA, and (conditionally) near-miss contrastive results.
2. **Runtime-compatible Gipformer correction.** Train on real single-best Gipformer
   errors, then test lexical retrieval and PiDA-style text corruption. Do not call
   acoustic perturbations “N-best.”
3. **Grounded Vietnamese SOAP generation.** Create provenance-preserving silver
   training data from MTS-Dialog and ACI-BENCH, extract facts before generation,
   and compare against the current CKey baseline.

Transcript candidates are ranked only after their safety gates pass: lowest
hard-split medical-term error wins, then overall WER, then latency. Do not stack a
direct ASR adapter and GEC until each passes independently.

## Boundaries and open evidence gaps

- `usage_scope=research_only` and `promotion_status=blocked_research_only` apply to
  every resulting dataset, checkpoint, metric report, and model bundle.
- Use public or synthetic data only. Never put CarePath consultation audio, patient
  data, or raw microphone captures in this pack, Colab Drive, or Hugging Face.
- The review found no peer-reviewed public Vietnamese consultation-to-SOAP corpus.
  Translated or teacher-generated examples are silver data and cannot demonstrate
  production readiness.
- Data rights and qualified Vietnamese clinician validation are separate promotion
  gates. A paper's open license is not a shortcut around either gate.
- Results from English, translation, oncology, or private deployed systems are
  hypotheses to test locally, not claims already proven for general Vietnamese
  outpatient care.
