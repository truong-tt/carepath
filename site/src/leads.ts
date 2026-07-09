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

export interface LeadSubmissionConfig {
  endpoint?: string;
  email?: string;
  fetcher?: typeof fetch;
  openMailto?: (url: string) => void;
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

export function buildLeadMailto(payload: LeadDraft, email = ""): string {
  const subject = `CarePath Translate pilot — ${payload.clinic}`;
  const body = [
    payload.message,
    "",
    `${payload.name} — ${payload.role}`,
    payload.contact,
    `${payload.clinic} — ${payload.specialty}`,
    payload.scenarioTitle,
    "",
    payload.transcript,
  ].join("\n");
  return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

export async function submitLead(
  payload: LeadDraft,
  {
    endpoint,
    email,
    fetcher = fetch,
    openMailto = (url) => {
      window.location.href = url;
    },
  }: LeadSubmissionConfig,
): Promise<"posted" | "mailto"> {
  if (endpoint) {
    const response = await fetcher(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Lead endpoint returned ${response.status}.`);
    }
    return "posted";
  }

  openMailto(buildLeadMailto(payload, email));
  return "mailto";
}
