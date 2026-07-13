import { describe, expect, it } from "vitest";
import { scenarios } from "./scenarios";
import { assertScenario } from "./scenarioSchema";

describe("scenario schema", () => {
  it("validates all bundled scripts", () => {
    expect(scenarios).toHaveLength(3);
    expect(scenarios.every((scenario) => scenario.turns.length === 8)).toBe(true);
  });

  it("rejects incomplete turns", () => {
    expect(() =>
      assertScenario({
        id: "broken",
        title: { vi: "Hỏng", en: "Broken" },
        summary: { vi: "Thiếu dữ liệu", en: "Missing data" },
        turns: [{ id: "turn-1" }],
      }),
    ).toThrow("incomplete turn");
  });

  it("rejects an ungated high-risk turn", () => {
    expect(() =>
      assertScenario({
        id: "unsafe",
        title: { vi: "Không an toàn", en: "Unsafe" },
        summary: { vi: "Thiếu chặn", en: "Missing gate" },
        turns: [
          {
            id: "turn-1",
            speaker: "doctor",
            sourceLanguage: "vi",
            vi: "Uống nửa viên.",
            en: "Take half a tablet.",
            riskTier: "high",
            riskSpans: [],
          },
        ],
      }),
    ).toThrow("ungated high-risk turn");
  });
});
