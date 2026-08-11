export interface RiskSpan {
  kind: string;
  severity: string;
  term: string;
  start?: number;
  end?: number;
}

export interface VisitTurn {
  id: string;
  session_id: string;
  seq: number;
  speaker: "doctor" | "patient" | string;
  src_lang: string;
  tgt_lang: string;
  source_text: string;
  normalized_text: string;
  translation: string;
  asr_confidence: number;
  mt_confidence: number;
  risk_tier: "low" | "medium" | "high" | "critical" | string;
  risk_spans: RiskSpan[];
  readback: {
    back_translation: string;
    entities: { kind: string; source_text: string; translated_text: string }[];
    flags: string[];
  } | null;
  status: string;
  corrected_text: string | null;
  created_at: string;
  /** Derived server-side and attached to turn_result; recomputed on replay. */
  requires_confirmation?: boolean;
  low_confidence?: boolean;
}

export interface SoapNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  missing_information: string[];
  review_required: boolean;
}

export interface PatientSummary {
  what_we_discussed: string;
  medications: string;
  follow_up: string;
  allergies_noted: string[];
  review_required: boolean;
}

export interface VisitNote {
  visit_id: string;
  turn_count: number;
  unconfirmed_turn_count: number;
  clinical_note: SoapNote;
  patient_summary: PatientSummary;
  metadata: Record<string, unknown>;
}

export interface PatientContext {
  age: string;
  sex: string;
  reason: string;
}

/**
 * Port of interpreter/frontend/src/tts.ts canSpeakTurn -- the same fail-closed
 * rule, not a reimplementation of it. A turn is spoken to the patient only once
 * it is confirmed (or was delivered as low risk), never while it is awaiting
 * confirmation, blocked, or flagged low confidence.
 */
export function canSpeakTurn(turn: VisitTurn, playbackSuppressed: boolean): boolean {
  return (
    !playbackSuppressed &&
    !turn.low_confidence &&
    !turn.requires_confirmation &&
    !["awaiting_confirm", "blocked", "ended"].includes(turn.status) &&
    ["delivered", "confirmed", "corrected"].includes(turn.status)
  );
}

/** Turns awaiting the clinician are masked from the patient pane entirely. */
export function isGated(turn: VisitTurn): boolean {
  return (
    turn.requires_confirmation === true ||
    ["awaiting_confirm", "blocked"].includes(turn.status)
  );
}

export function spokenText(turn: VisitTurn): string {
  return turn.corrected_text || turn.translation;
}
