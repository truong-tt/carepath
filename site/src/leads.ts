import type { Language, Scenario } from "./demo/types";

export type ProductInterest = "interpreter" | "scribe" | "both";

// Contact channel for the pilot lead form + footer. Values fall back to
// baked-in defaults so the conversion path works even when no env var is set;
// override VITE_LEAD_EMAIL / VITE_LEAD_PHONE to change them per deployment.
export const leadContact = {
  email: import.meta.env.VITE_LEAD_EMAIL?.trim() || "tranth3truong@gmail.com",
  phone: import.meta.env.VITE_LEAD_PHONE?.trim() || "+84827745579",
};

export const zaloHref = `https://zalo.me/${leadContact.phone.replace(/\D/g, "")}`;

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
  interest: ProductInterest;
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
  interest?: ProductInterest;
  fields?: Partial<Pick<LeadDraft, "name" | "role" | "contact" | "message">>;
}

export function defaultLeadMessage(
  clinic: string,
  specialty: string,
  scenario: Scenario,
  language: Language,
  interest: ProductInterest = "both",
): string {
  const product =
    interest === "both"
      ? language === "en"
        ? "CarePath Interpreter and Scribe"
        : "Phiên dịch khám bệnh trực tiếp và Ghi chép bệnh án AI"
      : language === "en"
        ? `CarePath ${interest === "scribe" ? "Scribe" : "Interpreter"}`
        : interest === "scribe"
          ? "Ghi chép bệnh án AI"
          : "Phiên dịch khám bệnh trực tiếp";
  const scenarioContext =
    interest === "scribe"
      ? ""
      : language === "en"
        ? ` using the “${scenario.title.en}” scenario`
        : ` với kịch bản “${scenario.title.vi}”`;
  if (language === "en") {
    return `I would like to discuss a ${product} pilot for ${clinic} (${specialty})${scenarioContext}.`;
  }
  return `Tôi muốn trao đổi về chương trình thí điểm ${product} cho ${clinic} (${specialty})${scenarioContext}.`;
}

export function buildLeadDraft({
  clinic,
  specialty,
  scenario,
  transcript,
  language,
  interest = "both",
  fields = {},
}: LeadDraftInput): LeadDraft {
  const includeInterpreterContext = interest !== "scribe";
  return {
    name: fields.name ?? "",
    clinic,
    role: fields.role ?? "",
    contact: fields.contact ?? "",
    message:
      fields.message ??
      defaultLeadMessage(clinic, specialty, scenario, language, interest),
    scenarioId: includeInterpreterContext ? scenario.id : "",
    scenarioTitle: includeInterpreterContext ? scenario.title[language] : "",
    specialty,
    transcript: includeInterpreterContext ? transcript : "",
    language,
    interest,
  };
}

export function buildLeadMailto(payload: LeadDraft, email = ""): string {
  const subject = `CarePath pilot (${payload.interest}) - ${payload.clinic}`;
  const body = [
    `Product interest: ${payload.interest}`,
    "",
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

  if (!email) {
    throw new Error("No lead endpoint or email is configured.");
  }

  openMailto(buildLeadMailto(payload, email));
  return "mailto";
}
