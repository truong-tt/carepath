import type { DemoTurn, Scenario } from "./types";

export function buildTranscript(
  scenario: Scenario,
  turns: DemoTurn[],
  corrections: Record<string, string> = {},
): string {
  const lines = [
    "CAREPATH TRANSLATE",
    "BẢN MÔ PHỎNG — KHÔNG PHẢI BẢN DỊCH TRỰC TIẾP",
    scenario.title.vi,
    scenario.title.en,
    "",
  ];

  for (const turn of turns) {
    const speaker = turn.speaker === "doctor" ? "Bác sĩ / Doctor" : "Bệnh nhân / Patient";
    lines.push(`[${speaker}]`, `VI: ${turn.vi}`, `EN: ${corrections[turn.id] ?? turn.en}`, "");
  }

  return `\uFEFF${lines.join("\n")}`;
}
