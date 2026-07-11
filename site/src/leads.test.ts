import { describe, expect, it, vi } from "vitest";
import { scenarios } from "./demo/scenarios";
import { buildLeadDraft, buildLeadMailto, submitLead } from "./leads";

describe("buildLeadDraft", () => {
  it("attaches the configured scenario and transcript only when requested", () => {
    const draft = buildLeadDraft({
      clinic: "Phòng khám Minh Tâm",
      specialty: "Tim mạch",
      scenario: scenarios[1],
      transcript: "VI: Không dị ứng\nEN: Not allergic",
      language: "vi",
      includeInterpreterContext: true,
    });

    expect(draft.scenarioId).toBe("allergy");
    expect(draft.interest).toBe("both");
    expect(draft.message).toContain("Kiểm tra dị ứng — xác nhận phủ định");
    expect(draft.transcript).toContain("Not allergic");
  });

  it("omits interpreter context by default", () => {
    const draft = buildLeadDraft({
      clinic: "Phòng khám Minh Tâm",
      specialty: "Tim mạch",
      scenario: scenarios[1],
      transcript: "VI: Không dị ứng\nEN: Not allergic",
      language: "vi",
    });

    expect(draft).toMatchObject({ scenarioId: "", scenarioTitle: "", transcript: "" });
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
    expect(draft.message).toContain("Ghi chép bệnh án AI");
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

describe("submitLead", () => {
  const draft = buildLeadDraft({
    clinic: "Phòng khám Minh Tâm",
    specialty: "Nội tổng quát",
    scenario: scenarios[0],
    transcript: "",
    language: "vi",
  });

  it("throws instead of opening an empty mail draft when no channel is configured", async () => {
    const openMailto = vi.fn();
    await expect(
      submitLead(draft, { endpoint: "", email: "", openMailto }),
    ).rejects.toThrow();
    expect(openMailto).not.toHaveBeenCalled();
  });

  it("opens a prefilled mail draft when an email is configured", async () => {
    const openMailto = vi.fn();
    const result = await submitLead(draft, {
      email: "pilot@example.com",
      openMailto,
    });
    expect(result).toBe("mailto");
    expect(openMailto).toHaveBeenCalledOnce();
  });
});
