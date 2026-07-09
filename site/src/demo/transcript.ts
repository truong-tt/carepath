import type { DemoTurn, Language, Scenario } from "./types";

export function buildTranscript(
  scenario: Scenario,
  turns: DemoTurn[],
  corrections: Record<string, string> = {},
  language: Language = "vi",
): string {
  const lines = [
    "CAREPATH",
    language === "vi"
      ? "BẢN MÔ PHỎNG — KHÔNG PHẢI BẢN DỊCH TRỰC TIẾP"
      : "SIMULATION — NOT A LIVE TRANSLATION",
    scenario.title[language],
    scenario.title[language === "vi" ? "en" : "vi"],
    "",
  ];

  for (const turn of turns) {
    const speaker =
      turn.speaker === "doctor"
        ? language === "vi"
          ? "Bác sĩ / Doctor"
          : "Doctor / Bác sĩ"
        : language === "vi"
          ? "Bệnh nhân / Patient"
          : "Patient / Bệnh nhân";
    lines.push(`[${speaker}]`, `VI: ${turn.vi}`, `EN: ${corrections[turn.id] ?? turn.en}`, "");
  }

  return `\uFEFF${lines.join("\n")}`;
}
