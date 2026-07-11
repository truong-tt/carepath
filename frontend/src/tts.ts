import type { TranscriptTurn } from "./types";

export function canSpeakTurn(turn: TranscriptTurn, playbackSuppressed: boolean): boolean {
  return !playbackSuppressed
    && !turn.low_confidence
    && !turn.requires_confirmation
    && !["awaiting_confirm", "blocked", "ended"].includes(turn.status)
    && ["delivered", "confirmed", "corrected"].includes(turn.status);
}

export function speakTurn(turn: TranscriptTurn, playbackSuppressed: boolean) {
  if (!canSpeakTurn(turn, playbackSuppressed)) {
    return;
  }
  if (!("speechSynthesis" in window)) {
    return;
  }
  const utterance = new SpeechSynthesisUtterance(turn.corrected_text || turn.translation);
  utterance.lang = turn.tgt_lang === "vi" ? "vi-VN" : "en-US";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
