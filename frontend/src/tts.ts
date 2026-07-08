import type { Turn } from "./types";

export function speakTurn(turn: Turn) {
  if (!("speechSynthesis" in window)) {
    return;
  }
  const utterance = new SpeechSynthesisUtterance(turn.corrected_text || turn.translation);
  utterance.lang = turn.tgt_lang === "vi" ? "vi-VN" : "en-US";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
