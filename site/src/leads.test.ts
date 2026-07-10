import { describe, expect, it } from "vitest";
import { scenarios } from "./demo/scenarios";
import { buildLeadDraft, buildLeadMailto } from "./leads";

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
    expect(draft.interest).toBe("both");
    expect(draft.message).toContain("Kiểm tra dị ứng — xác nhận phủ định");
    expect(draft.transcript).toContain("Not allergic");
  });

  it("omits interpreter context from Scribe-only leads", () => {
    const draft = buildLeadDraft({
      clinic: "Phòng khám Minh Tâm",
      specialty: "Tim mạch",
      scenario: scenarios[1],
      transcript: "VI: Không dị ứng\nEN: Not allergic",
      language: "vi",
      interest: "scribe",
    });

    expect(draft).toMatchObject({
      interest: "scribe",
      scenarioId: "",
      scenarioTitle: "",
      transcript: "",
    });
    expect(draft.message).toContain("CarePath Scribe");
    expect(draft.message).not.toContain(scenarios[1].title.vi);
  });

  it("includes product interest in the mail subject and body", () => {
    const draft = buildLeadDraft({
      clinic: "Phòng khám Minh Tâm",
      specialty: "Tim mạch",
      scenario: scenarios[0],
      transcript: "sample",
      language: "en",
      interest: "interpreter",
    });

    const mailto = decodeURIComponent(
      buildLeadMailto(draft, "pilot@example.com"),
    );
    expect(mailto).toContain("subject=CarePath pilot (interpreter)");
    expect(mailto).toContain("Product interest: interpreter");
  });
});
