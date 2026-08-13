import { describe, expect, it } from "vitest";
import { matchProviders, matchReason, PROVIDERS } from "./providers";

describe("curated providers", () => {
  it("ranks by the words the patient used", () => {
    const matched = matchProviders("itchy red rash on both arms since yesterday");
    expect(matched[0].id).toBe("cp-derm");
  });

  it("always offers general practice, including when nothing is recognised", () => {
    expect(matchProviders("I feel strange and I don't know why").map((p) => p.id)).toContain(
      "cp-gp",
    );
    expect(matchProviders("my tooth hurts").map((p) => p.id)).toContain("cp-gp");
  });

  it("does not pad the list with unrelated specialties", () => {
    // A dental clinic offered for a rash is noise dressed as choice.
    expect(matchProviders("itchy rash").map((p) => p.id)).not.toContain("cp-dental");
  });

  it("is deterministic, so the pitch shows the same clinics every run", () => {
    const once = matchProviders("rash").map((p) => p.id);
    const twice = matchProviders("rash").map((p) => p.id);
    expect(once).toEqual(twice);
  });

  it("never states availability", () => {
    const forbidden = /slot|available|appointment|book now|today at/i;
    for (const provider of PROVIDERS) {
      expect(`${provider.hours} ${provider.note} ${provider.focus}`).not.toMatch(forbidden);
    }
  });

  it("explains the match by service, never by diagnosis", () => {
    const derm = PROVIDERS.find((p) => p.id === "cp-derm")!;
    const reason = matchReason(derm, "itchy rash")!;

    expect(reason).toContain("dermatology");
    // Routing language, not clinical language: it says what the patient said
    // and what the clinic does, and draws no conclusion between them.
    expect(reason).not.toMatch(/you (have|likely|probably|may have)/i);
  });

  it("gives no reason rather than a manufactured one", () => {
    const dental = PROVIDERS.find((p) => p.id === "cp-dental")!;
    expect(matchReason(dental, "itchy rash")).toBeNull();
  });
});
