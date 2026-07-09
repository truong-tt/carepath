export type Language = "vi" | "en";
export type Speaker = "doctor" | "patient";
export type RiskTier = "low" | "medium" | "high" | "critical";

export interface LocalizedText {
  vi: string;
  en: string;
}

export interface RiskSpan {
  kind: string;
  vi: string;
  en: string;
}

export interface ReadbackEntity {
  kind: string;
  sourceText: string;
  translatedText: string;
}

export interface DemoTurn {
  id: string;
  speaker: Speaker;
  sourceLanguage: Language;
  vi: string;
  en: string;
  riskTier: RiskTier;
  riskSpans: RiskSpan[];
  readback?: {
    entities: ReadbackEntity[];
  };
  escalation?: boolean;
}

export interface Scenario {
  id: string;
  title: LocalizedText;
  summary: LocalizedText;
  turns: DemoTurn[];
}

export type PlaybackState =
  | "idle"
  | "playing"
  | "paused"
  | "awaiting-confirmation"
  | "escalated"
  | "complete";
