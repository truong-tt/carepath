import { describe, expect, it } from "vitest";

import { canSpeakTurn } from "./tts";
import type { TranscriptTurn } from "./types";

const turn: TranscriptTurn = {
  id: "turn-1", session_id: "session-1", seq: 1, speaker: "doctor", src_lang: "vi", tgt_lang: "en",
  source_text: "xin chào", normalized_text: "xin chào", translation: "hello", asr_confidence: 1, mt_confidence: 1,
  risk_tier: "low", risk_spans: [], readback: null, status: "delivered", corrected_text: null, created_at: new Date(0).toISOString(),
};

describe("canSpeakTurn", () => {
  it("allows only delivered or confirmed turns without safety blocks", () => {
    expect(canSpeakTurn(turn, false)).toBe(true);
    expect(canSpeakTurn({ ...turn, status: "confirmed", corrected_text: "hello there" }, false)).toBe(true);
    expect(canSpeakTurn({ ...turn, status: "corrected", corrected_text: "hello there" }, false)).toBe(true);
    expect(canSpeakTurn({ ...turn, low_confidence: true }, false)).toBe(false);
    expect(canSpeakTurn({ ...turn, requires_confirmation: true, status: "awaiting_confirm" }, false)).toBe(false);
    expect(canSpeakTurn({ ...turn, status: "ended" }, false)).toBe(false);
    expect(canSpeakTurn(turn, true)).toBe(false);
  });
});
