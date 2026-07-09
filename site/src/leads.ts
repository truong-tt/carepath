import type { Language, Scenario } from "./demo/types";

export interface LeadDraft {
  name: string;
  clinic: string;
  role: string;
  contact: string;
  message: string;
  scenarioId: string;
  scenarioTitle: string;
  specialty: string;
  transcript: string;
  language: Language;
}

interface LeadDraftInput {
  clinic: string;
  specialty: string;
  scenario: Scenario;
  transcript: string;
  language: Language;
  fields?: Partial<Pick<LeadDraft, "name" | "role" | "contact" | "message">>;
}

export function defaultLeadMessage(
  clinic: string,
  specialty: string,
  scenario: Scenario,
  language: Language,
): string {
  if (language === "en") {
    return `I would like to discuss a CarePath Translate pilot for ${clinic} (${specialty}) using the “${scenario.title.en}” scenario.`;
  }
  return `Tôi muốn trao đổi về chương trình thí điểm CarePath Translate cho ${clinic} (${specialty}) với kịch bản “${scenario.title.vi}”.`;
}

export function buildLeadDraft({
  clinic,
  specialty,
  scenario,
  transcript,
  language,
  fields = {},
}: LeadDraftInput): LeadDraft {
  return {
    name: fields.name ?? "",
    clinic,
    role: fields.role ?? "",
    contact: fields.contact ?? "",
    message:
      fields.message ??
      defaultLeadMessage(clinic, specialty, scenario, language),
    scenarioId: scenario.id,
    scenarioTitle: scenario.title[language],
    specialty,
    transcript,
    language,
  };
}
