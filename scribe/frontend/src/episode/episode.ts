/**
 * One care episode, held in the browser for the length of a tab.
 *
 * This is the spine the pivot needed: the visit, the prescription and the
 * follow-up were already separate working tools sharing a backend session id and
 * nothing a patient could see. The episode is what carries between them.
 *
 * `sessionStorage`, not `localStorage`, and not a table. Three reasons, in
 * order of weight:
 *
 * 1. Health data that outlives the tab is health data somebody has to be
 *    accountable for. Nothing here is worth that: every durable record already
 *    lives server-side as turns, and the patient's copy is a sheet they keep.
 * 2. It matches the existing decision one directory over — `carepath.visitId` in
 *    VisitScreen.tsx is sessionStorage for exactly this reason.
 * 3. A shared device in a clinic waiting room is the normal case, not the edge
 *    one. Closing the tab has to be enough.
 *
 * Fields are minimised on purpose. There is deliberately no name, passport,
 * date of birth, phone number or email: none of the six journey stages needs
 * one, so collecting one would be collecting for a workflow that does not exist.
 */

const KEY = "carepath.episode";

export type EpisodeStatus =
  | "planning"
  | "prepared"
  | "in_visit"
  | "post_visit"
  | "escalated";

/** Where an episode's content came from. Never inferred, always carried. */
export type EpisodeSource = "scripted" | "live";

export interface Provider {
  id: string;
  name: string;
  district: string;
  focus: string;
  languages: string[];
  hours: string;
  note: string;
}

export interface VisitBrief {
  concern: string;
  since: string;
  history: string;
  medications: string;
  allergies: string;
  questions: string;
  insurance: string;
}

/** A confirmed document line, in both languages, as the patient received it. */
export interface EpisodeDocument {
  id: string;
  kind: string;
  vi: string;
  en: string;
  isMedication: boolean;
  source: EpisodeSource;
}

export interface CareEpisode {
  id: string;
  status: EpisodeStatus;
  /** The patient's own language. Clinician surfaces stay Vietnamese regardless. */
  locale: "en" | "vi";
  location: string;
  careNeed: string;
  timing: string;
  insurance: boolean;
  provider?: Provider;
  visitBrief?: VisitBrief;
  /**
   * The clinician's side of the brief, where a Vietnamese version genuinely
   * exists. It does for the scripted scenario and not for text a patient types,
   * because nothing offline can translate free prose — and inventing a
   * Vietnamese line the patient never approved would put words in their mouth
   * in the one document a clinician reads before treating them. Absent means
   * "translated live at the start of the visit", which the brief screen says.
   */
  visitBriefVi?: Partial<VisitBrief>;
  /** Set only when a real visit ran; the scripted stage never writes one. */
  visitId?: string;
  documents: EpisodeDocument[];
  confirmedMedications: string[];
  followUp?: string;
  escalation?: { reason: string; requestedAt: string };
  /**
   * One flag, not a consent framework. The live tools collect their own consent
   * for translation and for document processing at the point they do it; the
   * only thing this module can consent to is keeping the episode in the browser.
   */
  consent: { storeEpisode: boolean };
  createdAt: string;
  source: EpisodeSource;
}

function makeId(): string {
  return `ep_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
}

export function newEpisode(seed: Partial<CareEpisode> = {}): CareEpisode {
  return {
    id: makeId(),
    status: "planning",
    locale: "en",
    location: "",
    careNeed: "",
    timing: "",
    insurance: false,
    documents: [],
    confirmedMedications: [],
    consent: { storeEpisode: true },
    createdAt: new Date().toISOString(),
    source: "live",
    ...seed,
  };
}

/**
 * Read the episode, or null.
 *
 * Never throws. A malformed value here would otherwise take out every screen
 * that reads it on mount, and the recovery a patient can perform is the same
 * either way: start again. So a bad value is treated as no value.
 */
export function loadEpisode(): CareEpisode | null {
  try {
    const raw = window.sessionStorage?.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CareEpisode;
    if (!parsed || typeof parsed !== "object" || typeof parsed.id !== "string") {
      return null;
    }
    // Arrays are read by index all over the journey screens; a truncated write
    // must not turn into `undefined.map`.
    return {
      ...parsed,
      documents: Array.isArray(parsed.documents) ? parsed.documents : [],
      confirmedMedications: Array.isArray(parsed.confirmedMedications)
        ? parsed.confirmedMedications
        : [],
    };
  } catch {
    return null;
  }
}

export function saveEpisode(episode: CareEpisode): CareEpisode {
  try {
    window.sessionStorage?.setItem(KEY, JSON.stringify(episode));
  } catch {
    // Storage disabled or full. The episode still lives in React state for this
    // screen; losing it on navigation is better than breaking the journey.
  }
  return episode;
}

/** Merge into the current episode, creating one if there is none. */
export function patchEpisode(patch: Partial<CareEpisode>): CareEpisode {
  return saveEpisode({ ...(loadEpisode() ?? newEpisode()), ...patch });
}

/**
 * Append confirmed document lines, and lift the medication ones into
 * `confirmedMedications`.
 *
 * Medication text is stored verbatim from the confirmed translation rather than
 * summarised. What a patient is told to swallow should be the clinician's own
 * confirmed words — the same rule `_confirmed_medication_lines` follows in
 * scribe/carepath/main.py, applied to the patient's copy.
 */
export function addDocuments(lines: EpisodeDocument[]): CareEpisode {
  const episode = loadEpisode() ?? newEpisode();
  const known = new Set(episode.documents.map((doc) => doc.id));
  const fresh = lines.filter((line) => !known.has(line.id));
  const medications = [
    ...episode.confirmedMedications,
    ...fresh.filter((line) => line.isMedication).map((line) => line.en),
  ];
  return saveEpisode({
    ...episode,
    documents: [...episode.documents, ...fresh],
    confirmedMedications: [...new Set(medications)],
  });
}

export function clearEpisode(): void {
  try {
    window.sessionStorage?.removeItem(KEY);
  } catch {
    /* nothing kept, nothing to clear */
  }
}
