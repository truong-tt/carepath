> Source: https://claude.ai/public/artifacts/3af319d8-e860-4c8c-aa6a-3954395f0bcd (saved 2026-07-08). This is the research basis for `history/PLAN.md`; read current product and safety instructions first, then consult the archived plan for MVP context.

# Vietnamese ↔ English Live Clinical Translator — MVP Research & Planning Report

# Executive Summary

We recommend building a **hybrid cascaded speech-translation pipeline** (Audio → ASR → normalization → glossary-constrained MT/LLM → safety/risk classifier → bilingual transcript + TTS) with a mandatory **human-interpreter fallback**, scoped narrowly to the **outpatient consultation + medication/follow-up explanation** stage of the clinical workflow. This directly confirms the client's starting hypothesis. The Vietnamese-medical-NLP research base is now strong enough to build on: verified public datasets exist for medical MT (MedEV, 358,796 sentence pairs), medical ASR (VietMed, 16h labeled + 2,200h unlabeled), code-switching speech (ViMedCSS, 34h/16,576 utterances), speech translation (MultiMed-ST, 290,000 samples), NER (ViMedNER, ViMQ), and QA (ViMedAQA 44,313 triplets, ViHealthQA 10,015 pairs), plus a domain BERT (ViHealthBERT) and a phonetically-informed augmentation method (PiDA) specifically targeting ASR-error propagation in Vietnamese ST.

The single most important finding: **published research and US federal guidance both conclude that unreviewed machine translation is not safe for high-stakes clinical communication.** In a 2025 BMJ Quality & Safety study (Kong M, et al., doi:10.1136/bmjqs-2024-018384) testing ChatGPT-4 and Google Translate on 50 sets (316 sentences) of emergency-department discharge instructions, up to 66% of Google-translated instruction sets (Russian) contained at least one inaccuracy, and the potential for harm reached ≤1% at the sentence level and ≤6% at the instruction-set level. The US HHS Office for Civil Rights "Dear Colleague" letter of December 5, 2024 — implementing the May 6, 2024 Section 1557 final rule, with full implementation due June 5, 2025, and expressly covering "machine translation, including artificial intelligence and emerging technologies" — states that machine translation of critical documents "must be reviewed by a qualified human translator to ensure accuracy," and absent review, patients "should be warned that the translated document may contain errors." The product must therefore be positioned as a **translation-and-verification aid with structured confirmation flows and interpreter escalation — never an autonomous diagnostic or advice tool.**

Recommended direction: build the hybrid architecture with replaceable adapter interfaces for every AI component, design a 500-utterance bilingual evaluation set weighted toward high-risk categories, measure against explicit thresholds, and only then run a supervised clinical pilot.

# Key Findings

1. **Vietnamese medical NLP is no longer greenfield.** The VinUniversity Medical MT group and others have released a coherent stack of datasets and models covering exactly our use case: MedEV (MT), ViMedCSS + PiDA + LLM-near-misses (code-switching ASR/ST), MultiMed-ST and VietMed (medical speech), ViMedNER/ViMQ (NER), and ViMedAQA/ViHealthQA (QA). We can fine-tune and benchmark rather than build from scratch.

2. **Cascaded pipelines beat end-to-end for low-resource Vietnamese, at the cost of error propagation.** On the strongest published low-resource comparison, an enhanced cascade reached 21.3 BLEU versus 17.97 BLEU for the best end-to-end system — a several-point advantage. Cascades are also debuggable, allow independent component swaps, and reuse large monolingual ASR and text-MT corpora. The main weakness — ASR errors propagating into MT — is directly addressable with phonetic augmentation (PiDA reports up to +2.04 BLEU on erroneous ASR output) and glossary/safety layers.

3. **Fine-tuned domain models decisively outperform generic tools.** On MedEV, fine-tuned vinai-translate scored 52.14 BLEU (En→Vi) and 42.38 BLEU (Vi→En) on test, beating Google Translate (47.86 / 39.26) and far exceeding ChatGPT gpt-3.5-turbo (~36 / ~33). This means a generic API is an acceptable Day-1 placeholder but a fine-tuned/glossary-constrained model is needed for clinical quality.

4. **Code-switching (English drug/procedure names inside Vietnamese speech) is a first-class failure mode**, not an edge case. ViMedCSS exists precisely because standard ASR mishandles English medical terms embedded in Vietnamese; the LLM-near-misses contrastive method reports >2% error-rate reductions at code-switch points.

5. **Regulation forces human-in-the-loop.** HHS Section 1557 (2024 final rule) requires qualified interpreters/translators for critical healthcare communication and that machine translation of critical content be reviewed by a qualified human; Vietnam's Decree 13/2023 (and the new PDP Law effective 1 January 2026) classify health data as sensitive personal data requiring explicit, informed, purpose-specific consent. Both regimes shape MVP design.

6. **Confirmation/read-back (teach-back) is an evidence-based safety mechanism** we can operationalize. Per AHRQ and Kessels (2003, J R Soc Med), patients immediately forget between 40% and 80% of the medical information they receive during office visits, and almost half of what they do retain is incorrect; structured teach-back materially improves comprehension and reduces readmissions. This is the clinical justification for our confirmation-mode feature.

# Literature Review Matrix

All entries verified against primary sources (arXiv, ACL Anthology, Hugging Face, GitHub, publisher pages, and the VinUni project page). Where a figure could not be independently confirmed it is marked *unverified*.

| Paper / Dataset | Primary source | Task | Languages | Dataset size | Domain | Model approach | Reported results | Relevance to MVP | Implementation idea | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| **PiDA: Phonetically-Informed Data Augmentation** (Nguyen et al., Interspeech 2026) | vinuni-medical-mt.github.io/#paper-pida; arXiv 2606.12911 | ST robustness / data augmentation | Vi→En | Uses FLEURS Vi-En (augmented) | Medical + general speech | Phonetic word-embedding substitutions to simulate ASR errors; fine-tune ST | Up to **+2.04 BLEU** over standard fine-tuning on erroneous ASR output; slight gain on clean text | Directly mitigates our #1 cascade risk (ASR→MT error propagation) | Apply PiDA-style augmentation when fine-tuning our MT component | Evaluated on FLEURS, not clinical dialogue; BLEU-level, not clinical-error metrics |
| **Contrastive Training with LLM-generated Near-Misses** (Nguyen & Truong et al., Interspeech 2026) | vinuni-medical-mt.github.io/#paper-near-misses; arXiv 2606.06985 | Code-switching ASR | Vi-En, Zh-En | CS-FLEURS (cmn-eng), ViMedCSS (vie-eng) | Medical CS speech | POI-aware contrastive training; Whisper-small + LoRA; multi-negative ranking loss | **>2%** reduction in general and CS-aware error rates vs standard LoRA fine-tuning | Improves recognition of English drug names embedded in Vietnamese | Use as ASR fine-tuning recipe for code-switch robustness | Whisper-small scale; gains reported as error-rate deltas |
| **ViMedCSS** (Nguyen et al., LREC 2026) | lrec2026-main-445; HF tensorxt/ViMedCSS | Code-switching ASR benchmark | Vi-En | **34 hours, 16,576 utterances**, ≥1 English medical term each, 5 medical topics | Medical CS speech | Benchmarks SOTA ASR; Vi-optimized vs multilingual pretraining vs combined | Vi-optimized best on general segments; multilingual best on English insertions; combined best balance | First CS benchmark = our accent/drug-name test data | Use as a core ASR benchmark set for code-switching error rate | 34h is modest; topic-limited lexicon |
| **MedEV / Improving Vi-En Medical MT** (Vo et al., LREC-COLING 2024) | aclanthology.org/2024.lrec-main.784; arXiv 2403.19161; HF nhuvo/MedEV | Medical MT | Vi-En | **358,796 sentence pairs** (340,897 train / 8,939 val / 8,960 test) | Medical text | Fine-tune vinai-translate, envit5, mBART; vs Google/ChatGPT | FT vinai-translate best: **52.14 BLEU En→Vi, 42.38 Vi→En (test)**; Google 47.86/39.26; ChatGPT ~36/~33 | Our core MT training/benchmark corpus | Fine-tune MT on MedEV; use test split in our harness | Text (not speech) domain; de-identified written medical text, not spoken dialogue |
| **Meddict** (VinUni; via arXiv 2509.15640) | arXiv 2509.15640 | Terminology lexicon | En-Vi | **>64,000 entries** | Medical terminology | Dictionary-augmented LLM prompting | Terminology-aware cues consistently improve domain translation | Seed for our medical glossary / terminology control | Import as glossary backbone for constrained decoding | License/coverage for spoken abbreviations unverified |
| **MultiMed-ST** (Le-Duc et al., EMNLP 2025) | aclanthology.org/2025.emnlp-main.599; arXiv 2504.03546; GitHub leduckhai/MultiMed-ST | Medical speech translation | Vi, En, De, Fr, Zh (all directions) | **290,000 samples** (largest medical MT/ST) | Medical speech | Whisper-family ASR + NMT; cascaded vs e2e, bilingual vs multilingual analysis | Largest many-to-many medical ST; extensive baselines (see paper) | Provides Vi↔En ST baselines + models we can benchmark against | Use as external ST baseline + additional training data | Translations LLM-generated (Gemini) — quality caveat; register is dialogue-transcribed |
| **VietMed** (Le-Duc et al., LREC-COLING 2024) | aclanthology.org/2024.lrec-main.1509; arXiv 2404.05659 | Medical ASR | Vi | **16h labeled + 1,000h unlabeled medical + 1,200h unlabeled general** | Medical speech | w2v2-Viet, XLSR-53-Viet pretraining/fine-tuning | XLSR-53-Viet cut WER from 51.8%→29.6% on test (>40% relative) | Core Vietnamese medical ASR model + benchmark | Candidate ASR adapter; covers all ICD-10 groups & accents | 16h labeled is small; 29.6% WER still high for clinical safety unaided |
| **ViHealthBERT** (Minh et al., LREC 2022) | aclanthology.org/2022.lrec-1.35; GitHub demdecuong/vihealthbert | Domain PLM (NER, acronym, FAQ) | Vi | Pretraining corpus + acrDrAid (135 keyword sets) + FAQSum | Vietnamese healthcare text | BERT pretraining; SOTA on NER/AD/FAQ | Outperforms general-domain PLMs on health tasks | Backbone for our medical NER / risk-term detection | Use for entity tagging in the safety layer | Text-domain; 2022 vintage |
| **ViMedNER** (Pham Van Duong et al., EAI INIS 2024) | publications.eai.eu/index.php/inis/article/view/5221; DOI 10.4108/eetinis.v11i3.5221 | Medical NER | Vi | **>8,000 annotated samples**; entities: disease, symptom, cause, diagnostic, treatment | Medical text (diagnosis/treatment) | PhoBERT, XLM-R, ViDeBERTa, ViPubMedDeBERTa, ViHealthBERT | XLM-R consistently best | Entity schema for highlighting symptoms/diseases | Fine-tune NER for key-term highlighting | Text source (web); no drug-dosage entities |
| **ViMQ** (Ta Duc Huy et al., ICONIP 2021) | arXiv 2304.14405; GitHub tadeephuy/ViMQ | Medical NER + intent | Vi | **9,000 questions**; entities SYMPTOM&DISEASE (13,253), MEDICAL_PROCEDURE (2,000), MEDICINE (979) | Patient medical questions (Vinmec) | Baselines + self-supervised span-noise training | Span-noise training +~3% F1 on ViMQ NER | Patient-side intent + entity extraction | Intent tags for routing/triage-lite; MEDICINE entities for glossary | Patient-authored text, not speech; small MEDICINE set |
| **ViMedAQA** (Tran et al., ACL 2024 SRW) | aclanthology.org/2024.acl-srw.31; HF tmnam20/ViMedAQA | Abstractive medical QA | Vi | **44,313 {paragraph, question, answer} triplets** (39,881/2,215/2,217); topics: disease 15,690, medicine 13,873, drug 9,780, body part 4,970 | Medical (YouMed) | 8 LLMs prompted (VinaLlama, Llama3, Gemma, PhoGPT, ViGPT) | VinaLlama-7B best avg 58.01 (En prompt); component BLEU 33.69, ROUGE-L 59.89 | Source of drug/disease QA phrasing; NOT for autonomous answers | Use to build glossary + test comprehension phrasing | QA generated by Gemini 1.0 then human-verified; not a safety-vetted advice source |
| **ViHealthQA** (Nguyen et al., KSEM 2022) | HF tarudesu/ViHealthQA; SpringerLink 10.1007/978-3-031-10986-7 | Health QA / IR | Vi | **10,015 question–answer passage pairs** (Vinmec, VnExpress) | Consumer health QA | SPBERTQA: SBERT + BM25, MNR loss | Two-stage system beats bag-of-words baselines | Consumer-health phrasing reference | Corpus for patient-question phrasing patterns | Consumer (not clinician) register; expert-answered forum text |
| **MultiMed (ASR)** (Le-Duc et al., 2024/2025) | arXiv 2409.14074 | Multilingual medical ASR | Vi, En, De, Fr, Zh | 150 hours across 5 languages | Medical speech | Attention encoder-decoder | Documents Vietnamese tone/vowel/dialect ASR error taxonomy | Evidence base for our failure-mode list | Cite for accent/tone robustness testing | Broad, not Vi-En clinical-dialogue specific |

# Vietnamese-Specific Failure Modes (≥25)

Severity scale: **Critical** (plausible serious harm), **High**, **Moderate**, **Low**. "Wrong output risk" describes the mistranslation that could occur.

| # | Failure mode | Example (Vietnamese) | Wrong output risk | Clinical severity | Detection / mitigation |
|---|---|---|---|---|---|
| 1 | **Negation dropped/flipped** | "Không dị ứng với penicillin" | "Allergic to penicillin" (negation lost) | Critical | Negation-cue detector; force explicit polarity in read-back; highlight "không/chưa/không còn" |
| 2 | **Allergy term mistranslated** | "Dị ứng thuốc kháng sinh" | "Antibiotic reaction" vs "allergy" ambiguity | Critical | Allergy-intent classifier; mandatory confirmation of allergen + reaction |
| 3 | **Dosage number error** | "Uống nửa viên" (half a tablet) | "one tablet" / "five tablets" | Critical | Numeric-entity preservation check; back-translate dose; require confirm |
| 4 | **Frequency error** | "Ngày hai lần" (twice a day) | "two days" / "once a day" | Critical | Frequency normalizer (times/day, interval); read-back |
| 5 | **Unit confusion (mg/ml/mcg)** | "Năm trăm mi-li-gam" | "500 ml" instead of "500 mg" | Critical | Unit dictionary; flag missing/implausible units |
| 6 | **Tone-based homophone (ASR)** | "má" vs "mà" vs "ma"; "nặng nhọc" vs "năng ngọng" | Wrong word entirely | High | Tonal LM rescoring; low-confidence flag; PiDA-style robustness |
| 7 | **English drug name inside Vietnamese (code-switch)** | "Uống Augmentin sau ăn" | Drug name garbled/omitted | Critical | ViMedCSS-style CS ASR; glossary pinning of drug names |
| 8 | **Look-alike/sound-alike drug** | "Losec" vs "Lasix"; "Celebrex" vs "Celexa" | Wrong medication dispensed | Critical | LASA drug list check; spell + purpose confirmation |
| 9 | **Laterality (left/right)** | "Đau chân trái" (left leg) | "right leg" | Critical | Laterality keyword lock (trái/phải); highlight + confirm |
| 10 | **Southern accent variation** | Southern "d/gi/v" merger, final consonants | ASR substitution errors | High | Accent-diverse ASR training; confidence flagging |
| 11 | **Central accent variation** | Strong Central tonal/vowel shifts | High WER | High | Accent-robust models; fallback to text entry |
| 12 | **Medical abbreviation (Vi)** | "HA" (huyết áp = BP), "TC" (tiểu cầu = platelets) | Expanded wrong / left literal | High | Abbreviation expansion dictionary; context disambiguation |
| 13 | **Pronoun/politeness (kinship terms)** | "Con uống thuốc chưa?" (con = child/you) | Wrong referent (I/you/he) | Moderate | Speaker-role tagging; default clinical 2nd-person "you" |
| 14 | **Ambiguous subject omission** | "Đã uống thuốc" (subject dropped) | Wrong actor (I/you/patient) | High | Force subject clarification in medication context |
| 15 | **Date/time expression** | "Tái khám sau mười ngày" | "after ten months" / wrong date | High | Temporal normalizer; echo concrete date |
| 16 | **Numbers: Vietnamese large-number grouping** | "Một trăm hai mươi" (120) | "100 and 20" / 1,220 | High | Number parser; digit read-back |
| 17 | **Fast doctor shorthand / elision** | Rapid clipped speech | Dropped words, merged entities | High | VAD + segmentation; ask to repeat if low confidence |
| 18 | **Mask/PPE-muffled speech** | Muffled consonants | Higher WER | High | Noise-robust ASR; confidence threshold → re-prompt |
| 19 | **Hospital background noise** | Overlapping speech, alarms | Insertion/deletion errors | High | Noise-robustness testing; push-to-talk isolation |
| 20 | **Symptom severity misrender** | "Đau dữ dội" (severe) vs "đau nhẹ" (mild) | Severity understated | Critical | Severity lexicon; highlight intensifiers |
| 21 | **Pregnancy status** | "Đang mang thai" / "có bầu" | Missed → unsafe drug advice | Critical | Pregnancy-flag detector; force surfacing |
| 22 | **Prior medical history compression** | Long comorbidity list | Omission of a condition | High | Entity-count check source vs target |
| 23 | **Red-flag symptom (chest pain/breathing)** | "Đau ngực", "khó thở" | Understated/omitted → missed emergency | Critical | Red-flag keyword trigger → escalate / interpreter |
| 24 | **Stop vs continue medication** | "Ngưng thuốc" vs "tiếp tục thuốc" | Opposite instruction | Critical | Action-verb polarity check; explicit confirm |
| 25 | **Route of administration** | "Nhỏ mắt" (eye drops) vs oral | Wrong route | Critical | Route lexicon; confirm route with dose |
| 26 | **Number+classifier ("viên/gói/ống")** | "Hai gói" (two sachets) vs viên (tablets) | Wrong form/count | High | Classifier-aware dose parsing |
| 27 | **Homophonic disease terms** | "sốt" (fever) vs "xót"; ASR tone loss | Wrong symptom | High | Tonal LM + medical prior |
| 28 | **Patient English accent variation** | Non-native English patient reply | En ASR errors | Moderate | Robust En ASR; patient read-back on key items |
| 29 | **Idiomatic body-location terms** | "đau bụng" (abdomen, broad) | Over-precise mistranslation (stomach) | Moderate | Preserve vagueness; clinician clarifies |
| 30 | **Diacritic loss in transcript** | "thuoc" vs "thuốc" | Wrong word / ambiguity | Moderate | Enforce diacritic restoration in normalization |

# Clinical Safety Plan (risk classification & mitigation)

Core principle: the app **translates and helps verify communication; it never diagnoses, prescribes, or gives autonomous medical advice.** Risk tier drives app behavior.

| Risk level | Scenario | Example | Recommended app behavior |
|---|---|---|---|
| **Low** | Logistics / non-clinical | Appointment time, directions, "Have you eaten?" | Translate normally; passive transcript; no special gating |
| **Medium** | Symptom history, general education | "Describe your symptoms", diet advice | Highlight key medical terms (NER); show confidence; allow quick correction |
| **High** | Medication, dosage, allergy, laterality, follow-up instructions | "Take half a tablet twice daily"; "Any drug allergies?" | **Require confirmation/read-back**; force numeric/unit/negation surfacing; log; offer interpreter |
| **Very high** | Consent, emergency/red-flag, mental-health crisis, breaking bad news | Chest pain, suicidal ideation, informed consent | **Halt autonomous mode; recommend/route to human interpreter**; display disclaimer; capture audit record |

**Design mechanisms:**
- **Confirmation/read-back flow:** for High-risk utterances, the app back-translates the critical entities (drug, dose, frequency, route, laterality, negation) and presents them for explicit doctor confirmation before the patient hears the final version — operationalizing the evidence-based teach-back method (which counters the 40–80% of verbal information patients immediately forget).
- **Low-confidence handling:** ASR/MT confidence below threshold → visibly flag, request repeat, or fall back to typed text; never silently emit a low-confidence critical instruction.
- **Escalation logic:** red-flag keyword lexicon + Very-high intent classification triggers a prominent "Get a human interpreter" action.
- **AI-use disclosure:** patient-facing notice at session start that AI translation is being used and may contain errors, with the right to request a human interpreter (aligns with the HHS OCR Section 1557 machine-translation warning expectation).
- **Audit & correction:** every High/Very-high utterance, its confidence, any doctor correction, and escalation events are logged for review; doctor corrections feed the improvement loop.
- **Anti-scope-creep:** the model is instructed and post-filtered never to generate diagnostic conclusions, drug recommendations, or advice not spoken by a clinician; it only translates and surfaces what was said.

# Compliance and Privacy Considerations

*This is a research-backed summary, not legal advice. Engage Vietnamese counsel and US health-privacy counsel before any pilot.*

| Jurisdiction | Requirement | Relevance to app | MVP implication | Open legal question |
|---|---|---|---|---|
| **Vietnam — Decree 13/2023 (PDPD)** | Explicit, voluntary, purpose-specific consent; health/medical data is sensitive personal data with stricter safeguards | Recording + AI processing of clinical speech = processing sensitive data | Build explicit consent capture; appoint data-protection responsibility; minimize data | Is spoken clinical audio "sensitive personal data" requiring a DPIA in our exact configuration? |
| **Vietnam — PDP Law (effective 1 Jan 2026)** | Elevates Decree 13 to statute; stricter compliance, DPIA/TIA, DPO duties; sector-specific AI rules; grace period for small firms | Governs any Vietnam deployment/pilot | Design for PDP Law from day one; verify DPO/DPIA obligations | Exact sensitive-data enumeration delegated to government decree — pending |
| **Vietnam — cross-border transfer** | Transfer of Vietnamese citizens' data abroad requires impact-assessment dossier + safeguards | Cloud ASR/MT/LLM APIs hosted abroad | Prefer in-country/on-prem processing; if using foreign APIs, prepare transfer dossier | Which cloud regions/vendors satisfy MPS requirements? |
| **Vietnam — breach notification** | Report breaches to Ministry of Public Security (Decree 13: 72h; PDP Law relaxes strict 72h) | Audio/transcript store is a breach target | Encryption, access controls, incident plan | Final breach-notification timeline under PDP Law guiding decree |
| **US — HIPAA** | Audio/transcript = PHI; safeguards, minimum necessary; Business Associate Agreement required with any vendor handling PHI | US clinic deployment | BAA with every ASR/MT/TTS/LLM vendor; encryption; access logging | Is the app a Business Associate or a conduit? |
| **US — Section 1557 (2024 final rule)** | Qualified interpreter/translator for critical communication; **machine translation of critical content must be reviewed by a qualified human**; warn of possible errors (HHS OCR Dec 5, 2024 letter; full implementation June 5, 2025) | Defines when our app alone is insufficient | Position as aid + interpreter fallback; display error warning; human review for critical content | Does live AI interpretation count as "machine translation" under 1557, and what review satisfies it? |
| **US — language access / Title VI** | Meaningful access; may not require patients to supply own interpreter; free, timely, accurate services | Our app cannot replace mandated interpreter services | Offer, don't force; interpreter fallback must be free/accessible | Threshold defining "critical" vs routine communication |
| **Both — data minimization / retention** | Store least data, shortest time | Sensitive audio is highest-risk asset | **Privacy mode: no audio storage by default**; ephemeral processing; configurable retention | Minimum retention needed for audit vs deletion duty |

# MVP Architecture Recommendation

**Recommended: Option C — Hybrid cascaded pipeline + medical glossary + safety layer + LLM reviewer fallback**, with every AI component behind a replaceable adapter interface.

| Architecture | Pros | Cons | Debuggability | Latency | Safety | MVP suitability |
|---|---|---|---|---|---|---|
| **A. Pure cascade** (ASR→norm→MT→TTS) | Modular; reuses big corpora; best low-resource quality; each stage swappable | ASR errors propagate; more moving parts | High (inspect each stage) | Moderate (sum of stages) | Moderate alone | Good base, insufficient alone |
| **B. End-to-end ST** | Lower latency; simpler deploy; less explicit propagation | Needs large aligned Vi-En speech; opaque; hard to insert glossary/safety; lower low-resource quality | Low (black box) | Low | Hard to gate | Not yet for clinical safety |
| **C. Hybrid (cascade + glossary + safety + LLM reviewer)** | Cascade quality + terminology control + risk gating + fallback review; auditable | Most components to build; must manage latency | High | Moderate (optimize with streaming) | **Highest** — explicit safety layer & read-back | **Recommended** |

**Rationale:** Low-resource Vietnamese-English evidence favors cascades on quality (21.3 vs 17.97 BLEU in the strongest published comparison), and clinical safety requires the ability to insert a glossary, run NER/risk classification, and gate high-risk output — which end-to-end models make difficult. The hybrid keeps cascade quality while adding the safety scaffolding regulation demands.

**Components (each behind an adapter interface):**
1. **Vietnamese ASR** — candidate: PhoWhisper / XLSR-53-Viet / Whisper fine-tuned on VietMed + ViMedCSS.
2. **English ASR** — Whisper-family, robust to non-native patient accents.
3. **Text normalization** — numbers, units, dates, diacritic restoration, punctuation/segmentation.
4. **Translation (MT/LLM)** — fine-tuned vinai-translate (MedEV) or glossary-constrained LLM; PiDA-style augmentation for ASR-error robustness.
5. **Medical terminology control / glossary** — Meddict-seeded (>64,000 entries), drug-name pinning, LASA list.
6. **Medical NER** — ViHealthBERT / ViMedNER schema for key-term highlighting.
7. **Safety / risk classifier** — utterance risk tier + red-flag + negation/dosage/laterality checks.
8. **TTS** — Vietnamese and English.
9. **Bilingual transcript** — aligned, timestamped, correction-friendly.
10. **LLM reviewer fallback** — second-pass check of critical entities (dose/negation/allergen) and back-translation.
11. **Evaluation harness + feedback loop + admin review dashboard.**

# Benchmark and Evaluation Plan

| Component | Metric | Test data | MVP target threshold | Reviewer |
|---|---|---|---|---|
| Vi ASR | WER | VietMed test + our 500-set (Vi) | ≤15% general; ≤10% on key terms *(target, to calibrate)* | ASR engineer + Vi clinician |
| En ASR | WER | 500-set (En, accented) | ≤12% *(target)* | ASR engineer |
| ASR | Medical-term error rate | ViMedCSS + curated drug list | ≤5% on drug names | Clinician |
| ASR | Drug-name recognition rate | LASA + local formulary list | ≥95% exact | Pharmacist |
| ASR | Code-switch error rate | ViMedCSS | ≤ standard-model baseline − 2% | ASR engineer |
| ASR | Accent robustness (N/C/S) | Accent-stratified subset | No region >1.5× best-region WER | Vi linguist |
| ASR | Noise robustness | Mask/hospital-noise augmented | <1.5× clean WER | ASR engineer |
| MT | Medical terminology accuracy | 500-set high-risk | ≥98% on drug/dose/allergen terms | Clinician + pharmacist |
| MT | Dosage preservation | Dosage utterances | 100% exact number+unit | Pharmacist |
| MT | Negation preservation | Negation utterances | 100% polarity correct | Clinician |
| MT | Number/unit preservation | Numeric utterances | 100% | Reviewer |
| MT | Symptom accuracy | Symptom utterances | ≥95% | Clinician |
| MT | BLEU / COMET | MedEV test + 500-set | BLEU ≥ MedEV FT baseline (52 En→Vi / 42 Vi→En) *(as reference)* | NLP engineer |
| MT | Human medical reviewer score | 500-set | ≥4/5 adequacy on high-risk | Bilingual clinician |
| MT | Clinical error severity | 500-set | **Zero** critical-harm errors uncaught by safety layer | Clinical lead |
| End-to-end | Latency | Live simulation | ≤3–5 s per turn *(usability target)* | Product + engineer |
| End-to-end | Critical-info preservation | High-risk scripts | 100% surfaced/confirmed | Clinical lead |
| End-to-end | Conversation usability (SUS-style) | Mock clinics | ≥ agreed usability bar | UX researcher |
| End-to-end | Doctor trust rating | Post-session survey | Tracked baseline | UX researcher |
| End-to-end | Patient comprehension | Teach-back check | ≥ agreed bar | Clinician |
| End-to-end | Escalation correctness | Very-high scripts | ≥95% correct escalation, no missed red-flags | Clinical lead |

# 500-Utterance Evaluation Set Design

Bilingual: each category includes Vietnamese doctor utterances and English patient utterances. Includes **≥50 high-risk utterances** across dosage, allergies, negation, pregnancy, chest pain, breathing difficulty, drug names, left/right, time/frequency, stop/continue medication.

| Category | N | Example (Vi doctor) | Example (En patient) | Risk | Expected translation criteria | Failure cases to test |
|---|---|---|---|---|---|---|
| Greeting/logistics | 30 | "Chào anh, mời ngồi." | "My appointment was at 2pm." | Low | Natural, polite; pronoun handled | Kinship pronoun; time parsing |
| Chief complaint | 50 | "Anh thấy khó chịu ở đâu?" | "I've had a cough for a week." | Medium | Symptom + duration preserved | Duration units; vague location |
| Symptom description | 70 | "Đau dữ dội hay âm ỉ?" | "It's a sharp pain on my right side." | Medium–High | Severity + laterality exact | Severity lexicon; left/right |
| Medical history | 50 | "Anh từng mổ tim chưa?" | "I had heart surgery in 2019." | High | Negation + history complete | Negation; omission of comorbidity |
| Medication history | 50 | "Anh đang uống thuốc gì?" | "I take metformin and Lasix." | High | Drug names exact (code-switch) | LASA (Lasix/Losec); CS ASR |
| Allergy checking | 40 | "Anh có dị ứng thuốc nào không?" | "I'm allergic to penicillin." | Critical | Allergen + negation exact | Negation flip; allergen garble |
| Diagnosis explanation | 50 | "Kết quả cho thấy anh bị viêm phổi." | "Does that mean it's serious?" | Medium–High | Faithful; no added advice | Severity; scope-creep into advice |
| Medication instructions | 70 | "Uống một viên sau ăn sáng." | "Do I take it with food?" | Critical | Dose+route+timing exact; confirm | Route; timing; classifier |
| Dosage/frequency/date/time | 50 | "Nửa viên, ngày hai lần, trong mười ngày." | "For how many days?" | Critical | Number+unit+frequency+duration exact | Half-dose; twice/day; 10 days |
| Follow-up & red flags | 40 | "Nếu đau ngực hay khó thở, đến cấp cứu ngay." | "I've been having chest pain." | Critical/Very-high | Red-flag preserved; escalate | Missed red-flag; escalation trigger |

**High-risk subset (≥50):** dosage errors (half/double), allergy negation, "không/ngưng/tiếp tục thuốc" (stop/continue), pregnancy ("đang mang thai"), chest pain ("đau ngực"), breathing difficulty ("khó thở"), LASA drug pairs, laterality ("trái/phải"), frequency/time, and unit conversions (mg/ml/mcg).

# MVP Feature Prioritization

| Feature | Priority | Why | Complexity | Safety impact | MVP inclusion |
|---|---|---|---|---|---|
| Push-to-talk doctor mode | P0 | Core input; controls turn-taking; reduces noise | Low | Medium | **Build now** |
| Push-to-talk patient mode | P0 | Bidirectional core | Low | Medium | **Build now** |
| Vi↔En translation | P0 | The product | High | High | **Build now** |
| Live bilingual transcript | P0 | Verifiability, audit, correction | Medium | High | **Build now** |
| Spoken translation (TTS) | P0 | Patient/doctor comprehension | Medium | Medium | **Build now** |
| Medical glossary | P0 | Terminology accuracy; drug pinning | Medium | High | **Build now** |
| High-risk term highlighting | P0 | Draws attention to danger points | Medium | High | **Build now** |
| Confirmation/read-back mode | P0 | Evidence-based error catch on critical entities | Medium | Critical | **Build now** |
| Low-confidence warning | P0 | Prevents silent critical errors | Low–Medium | Critical | **Build now** |
| Human-interpreter fallback button | P0 | Regulatory + very-high-risk safety | Low | Critical | **Build now** |
| Privacy mode (no audio storage by default) | P0 | Decree 13 / HIPAA data minimization | Medium | High | **Build now** |
| Feedback button (wrong translation) | P1 | Improvement loop; audit | Low | Medium | **Build now (basic)** |
| Visit summary | P1 | Useful, but risk of unreviewed documentation | Medium | Medium | **Later** |
| Admin dashboard (review failed translations) | P1 | Auditing, QA, model improvement | Medium | High | **Build now (minimal) / expand later** |
| Emergency triage, consent, mental-health, pediatric emergency, autonomous advice/diagnosis | — | Out of scope; too high-risk | — | — | **Not now** |

# 8-Week MVP Roadmap

- **Week 1 — Research & scope:** finalize literature matrix; map clinical workflow; build risk register; assemble initial glossary from Meddict + LASA + local formulary; confirm consultation+medication scope.
- **Week 2 — Evaluation & architecture:** design and begin annotating the 500-utterance eval set (recruit bilingual clinician annotators); lock hybrid architecture; define adapter API spec for every AI component; draft UX flows including confirmation and interpreter fallback.
- **Weeks 3–4 — Basic prototype:** push-to-talk UI (both modes); wire ASR→normalization→MT→transcript→TTS through adapters; **mock provider mode** for deterministic tests; session logging with privacy mode default-on.
- **Weeks 5–6 — Safety layer:** integrate glossary matching, NER, risk classifier, high-risk highlighting, confirmation/read-back flow, low-confidence handling; build evaluation dashboard + feedback capture; wire interpreter-fallback trigger.
- **Week 7 — Simulated clinical testing:** run mock Vi-doctor/En-patient conversations; accent (N/C/S) and mask/noise testing; bilingual-reviewer scoring against thresholds; log critical-error and escalation-correctness metrics.
- **Week 8 — Pilot readiness:** evaluation report vs thresholds; documented known limitations; privacy-policy and consent-flow draft (for counsel review); written pilot protocol with supervising clinicians and interpreter on standby. **Go/no-go gate: zero uncaught critical-harm errors.**

# Historical Codex Implementation Tickets

The tickets below describe the original pre-restructure MVP layout. They are
historical research context only; use `AGENTS.md` and the current `scribe/`,
`interpreter/`, `shared/`, and `scribe/training/` directories for implementation.

**Epic 1 — Repository setup.** *Title:* Monorepo scaffold with adapter contracts. *Background:* All AI components must be swappable. *Scope:* Monorepo (backend, frontend, shared types); linting/CI; env config; `providers/` package defining abstract adapter interfaces (ASR, MT, TTS, NER, RiskClassifier). *Acceptance:* CI green; abstract interfaces importable; mock implementations registered. *Tests:* interface conformance tests. *Files:* `/backend`, `/frontend`, `/packages/providers`. *Edge cases:* version pinning; secrets never committed.

**Epic 2 — Backend API.** *Title:* Session & turn API. *Scope:* REST/WebSocket endpoints: create session, submit audio turn, receive transcript+translation+risk, confirm turn, escalate. *Acceptance:* streaming turn returns transcript, translation, confidence, risk tier. *Tests:* contract tests with mock providers; WS reconnect. *Files:* `backend/api/`, `backend/session/`. *Edge cases:* dropped audio, partial turns, concurrent sessions.

**Epic 3 — Frontend push-to-talk UI.** *Title:* Dual push-to-talk interface. *Scope:* Doctor/patient modes, mic capture, turn indicator, bilingual transcript view, risk highlighting, confirm + interpreter buttons. *Acceptance:* full turn round-trips in mock mode. *Tests:* component + e2e. *Files:* `frontend/components/`. *Edge cases:* mic permission denial; rapid mode switching.

**Epic 4 — Audio recording & playback.** *Scope:* capture, encode, stream; TTS playback; privacy-mode no-persist path. *Acceptance:* audio streamed and discarded by default. *Tests:* format, buffering, retention flag. *Edge cases:* long turns; low bandwidth.

**Epic 5 — ASR adapter interface.** *Scope:* `transcribe(audio, lang) → {text, confidence, tokens}`; implementations for mock + one Vi + one En engine. *Acceptance:* language routing; confidence surfaced. *Tests:* golden-audio fixtures; WER harness hook. *Edge cases:* code-switch, silence, noise.

**Epic 6 — Translation adapter interface.** *Scope:* `translate(text, src, tgt, glossary) → {text, confidence, alignments}`; mock + fine-tuned/glossary-constrained impl. *Acceptance:* glossary terms forced. *Tests:* negation/number/unit preservation cases. *Edge cases:* empty input, untranslatable tokens.

**Epic 7 — TTS adapter interface.** *Scope:* `synthesize(text, lang) → audio`. *Acceptance:* Vi & En playback. *Tests:* latency, caching. *Edge cases:* long text, special chars/diacritics.

**Epic 8 — Transcript data model.** *Scope:* turn schema (speaker, lang, source text, translation, confidence, risk, corrections, timestamps). *Acceptance:* aligned bilingual render; audit fields. *Tests:* serialization; migration. *Edge cases:* edited turns, retractions.

**Epic 9 — Medical glossary.** *Scope:* import Meddict + LASA + formulary; lookup + fuzzy match API. *Acceptance:* drug-name pinning works. *Tests:* LASA collision cases. *Edge cases:* multi-word terms, abbreviations.

**Epic 10 — Risk term detector.** *Scope:* NER + rules for dose/negation/laterality/red-flag/pregnancy; returns risk tier + spans. *Acceptance:* tiers match labeled fixtures. *Tests:* per-failure-mode fixtures. *Edge cases:* nested entities; negation scope.

**Epic 11 — High-risk highlighting UI.** *Scope:* render risk spans; color/severity; require acknowledgment for critical. *Acceptance:* critical terms visually blocked until confirmed. *Tests:* rendering; a11y. *Edge cases:* overlapping spans.

**Epic 12 — Confirmation/read-back flow.** *Scope:* for High/Very-high turns, back-translate critical entities and present for doctor confirm before patient TTS. *Acceptance:* no critical turn reaches patient unconfirmed. *Tests:* dosage/allergy/negation scripts. *Edge cases:* doctor edits mid-confirm.

**Epic 13 — Session storage.** *Scope:* privacy-mode default no-audio; configurable retention; encryption at rest. *Acceptance:* audio not persisted by default; transcripts encrypted. *Tests:* retention policy; deletion. *Edge cases:* legal-hold vs delete conflict.

**Epic 14 — Feedback capture.** *Scope:* per-turn "wrong translation" flag with reason. *Acceptance:* feedback stored + linked to turn. *Tests:* submission; dashboard surfacing. *Edge cases:* feedback on redacted turns.

**Epic 15 — Evaluation harness.** *Scope:* run 500-set + MedEV/ViMedCSS through pipeline; compute WER, BLEU/COMET, term/dose/negation preservation, escalation correctness, clinical error severity. *Acceptance:* reproducible report vs thresholds. *Tests:* metric unit tests; fixtures. *Edge cases:* missing refs; partial pipelines.

**Epic 16 — Mock provider mode.** *Scope:* deterministic mock ASR/MT/TTS/NER for CI and demos. *Acceptance:* full flow offline. *Tests:* determinism. *Edge cases:* injected error scenarios.

**Epic 17 — Admin dashboard.** *Scope:* review failed/low-confidence/escalated turns; filter by risk; export. *Acceptance:* reviewers see corrections + feedback. *Tests:* auth; pagination. *Edge cases:* PHI redaction in views.

**Epic 18 — Privacy controls.** *Scope:* consent capture at session start; AI-use disclosure; data-minimization toggles; deletion endpoint. *Acceptance:* consent required before recording; disclosure logged. *Tests:* consent gating; deletion. *Edge cases:* withdrawn consent mid-session.

# Open Questions (for human experts, doctors, legal counsel, pilot partners)

1. **Legal (Vietnam):** Does our exact configuration require a DPIA under Decree 13 / PDP Law, and what cloud regions/vendors satisfy MPS cross-border-transfer rules? Final breach-notification timeline under the PDP Law guiding decree?
2. **Legal (US):** Does live AI interpretation fall under Section 1557's "machine translation" review requirement, and what human-review workflow satisfies it? Is the app a HIPAA Business Associate?
3. **Clinical:** What is the acceptable maximum WER/error rate before a clinician trusts the transcript? Which specific red-flag phrases must always trigger escalation? Who is liable for a mistranslation-driven error?
4. **Formulary:** Which local Vietnamese drug names/brands and LASA pairs must be pinned in the glossary?
5. **Metrics:** What clinical-error-severity rubric and threshold gate the pilot (we propose zero uncaught critical-harm errors)?
6. **Model:** Do we fine-tune ASR on VietMed+ViMedCSS in-house or license a vendor with a BAA/data-residency guarantee?
7. **Data:** Can we ethically collect a small real (consented, de-identified) clinical Vi-En dialogue set to supplement MedEV (text) and MultiMed-ST (LLM-translated) for evaluation realism?
8. **Pilot:** Which partner clinic, supervising clinicians, and on-standby interpreters will support the supervised pilot?

---
*Verification note:* All dataset sizes, BLEU/WER figures, and citations above were confirmed against primary sources (arXiv, ACL Anthology, Hugging Face, GitHub, publisher pages, and the VinUni Medical MT project page). Interspeech 2026 arXiv IDs (2606.12911, 2606.06985) and the ViMedCSS arXiv ID (2602.12911) are as listed on the VinUni project page; note the project page reuses the MedEV arXiv ID (2403.19161) as a link for ViMedCSS, which appears to be a site error — the verified ViMedCSS venue is LREC 2026 (pages 5657–5665, DOI 10.63317/58uwrquo3znb). Target thresholds marked *(target)* are proposed by this report and must be calibrated with clinical partners, not drawn from a published standard.
