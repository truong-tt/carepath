import { describe, expect, it } from "vitest";
import { scenarios } from "./demo/scenarios";
import { buildLeadDraft } from "./leads";

describe("buildLeadDraft", () => {
  it("attaches the configured scenario and transcript", () => {
    const draft = buildLeadDraft({
      clinic: "Phòng khám Minh Tâm",
      specialty: "Tim mạch",
      scenario: scenarios[1],
      transcript: "VI: Không dị ứng\nEN: Not allergic",
      language: "vi",
    });

    expect(draft.scenarioId).toBe("allergy");
    expect(draft.message).toContain("Kiểm tra dị ứng — xác nhận phủ định");
    expect(draft.transcript).toContain("Not allergic");
  });
});
