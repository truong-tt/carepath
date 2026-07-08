export type SessionCreateResponse = {
  session_id: string;
};

export type Turn = {
  id: string;
  session_id: string;
  seq: number;
  speaker: "doctor" | "patient";
  src_lang: string;
  tgt_lang: string;
  source_text: string;
  normalized_text: string;
  translation: string;
  asr_confidence: number;
  mt_confidence: number;
  risk_tier: "low" | "medium" | "high" | "critical";
  risk_spans: RiskSpan[];
  readback: Readback | null;
  status: string;
  corrected_text: string | null;
  created_at: string;
};

export type RiskSpan = {
  start: number;
  end: number;
  kind: string;
  severity: "low" | "medium" | "high" | "critical";
  term: string;
};

export type Readback = {
  back_translation: string;
  entities: Array<{
    kind: string;
    source_span: [number, number];
    translated_span: [number, number];
  }>;
  flags: string[];
};

export type TranscriptTurn = Turn & {
  low_confidence?: boolean;
  requires_confirmation?: boolean;
};

export type WsEvent =
  | { type: "session_state"; turns: Turn[] }
  | {
      type: "turn_result";
      turn: Turn;
      requires_confirmation: boolean;
      low_confidence: boolean;
    }
  | { type: "turn_error"; message: string; retryable: boolean };
