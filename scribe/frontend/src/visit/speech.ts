// Speech capture runs in the browser, not on the server.
//
// The consequence that matters clinically: no audio ever leaves the device on
// this path. There is no upload, no temp file, and nothing to retain. The
// differentiated pipeline -- normalization, glossary, translation, risk
// classification, clinician confirmation -- all still runs server-side on the
// recognised text.

export interface SpeechResult {
  transcript: string;
  /** Undefined when the browser does not report one; never faked. */
  confidence?: number;
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEventLike {
  results: ArrayLike<ArrayLike<{ transcript: string; confidence?: number }>>;
}

function recognitionCtor(): SpeechRecognitionCtor | undefined {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

export function speechSupported(): boolean {
  return recognitionCtor() !== undefined;
}

export const BCP47: Record<string, string> = { vi: "vi-VN", en: "en-US" };

export interface SpeechSession {
  stop(): void;
  abort(): void;
}

/**
 * Listen for one utterance.
 *
 * Resolves through `onResult` when speech is recognised, and always calls
 * `onEnd` so the caller can clear its recording state even on error. Errors are
 * reported rather than thrown: the typed fallback beside every microphone
 * button is the recovery path, so a failed recognition must never break the
 * visit.
 */
export function listenOnce(
  lang: string,
  handlers: {
    onResult: (result: SpeechResult) => void;
    onError?: (code: string) => void;
    onEnd?: () => void;
  },
): SpeechSession | null {
  const Ctor = recognitionCtor();
  if (!Ctor) return null;

  const recognition = new Ctor();
  recognition.lang = BCP47[lang] ?? lang;
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const best = event.results?.[0]?.[0];
    if (!best?.transcript) return;
    // Some browsers report confidence 0 for a perfectly good result. Reporting
    // that as-is would flag every turn low-confidence, so treat a falsy value
    // as "not reported" and let the server default it.
    const confidence =
      typeof best.confidence === "number" && best.confidence > 0 ? best.confidence : undefined;
    handlers.onResult({ transcript: best.transcript.trim(), confidence });
  };
  recognition.onerror = (event) => handlers.onError?.(event.error ?? "unknown");
  recognition.onend = () => handlers.onEnd?.();

  try {
    recognition.start();
  } catch {
    handlers.onError?.("start-failed");
    handlers.onEnd?.();
    return null;
  }
  return {
    stop: () => recognition.stop(),
    abort: () => recognition.abort(),
  };
}

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

let activeAudio: HTMLAudioElement | null = null;

function browserSpeak(text: string, lang: string): void {
  if (typeof window.speechSynthesis === "undefined") return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = BCP47[lang] ?? lang;
  window.speechSynthesis.speak(utterance);
}

/**
 * Does this browser have a voice for the language, at all?
 *
 * A default Windows or macOS install ships no vi-VN voice, and asking
 * SpeechSynthesis to speak Vietnamese without one produces either silence or
 * Vietnamese read with English phonemes. Neither is acceptable in front of a
 * patient, so we check before trusting it.
 */
export function hasVoiceFor(lang: string): boolean {
  const voices = window.speechSynthesis?.getVoices?.() ?? [];
  const prefix = (BCP47[lang] ?? lang).slice(0, 2).toLowerCase();
  return voices.some((voice) => voice.lang.toLowerCase().startsWith(prefix));
}

/**
 * Speak text to the patient. Only ever called for confirmed turns.
 *
 * Vietnamese goes through the server voice, because the browser usually has
 * none. Any failure falls back to SpeechSynthesis rather than leaving the
 * consultation silent.
 */
export async function speak(text: string, lang: string): Promise<void> {
  if (!lang.toLowerCase().startsWith("vi")) {
    browserSpeak(text, lang);
    return;
  }
  try {
    const response = await fetch(`${API_BASE}/api/v1/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, lang: "vi" }),
    });
    if (!response.ok) throw new Error(String(response.status));
    const url = URL.createObjectURL(await response.blob());
    cancelSpeech();
    const audio = new Audio(url);
    activeAudio = audio;
    audio.onended = () => URL.revokeObjectURL(url);
    await audio.play();
  } catch {
    browserSpeak(text, lang);
  }
}

export function cancelSpeech(): void {
  window.speechSynthesis?.cancel();
  if (activeAudio) {
    activeAudio.pause();
    activeAudio = null;
  }
}
