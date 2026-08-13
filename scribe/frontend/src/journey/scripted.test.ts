import { describe, expect, it } from "vitest";
import { canSpeakTurn, isGated, spokenText } from "../visit/types";
import { confirmScripted, SCRIPTED_DOCUMENT, SCRIPTED_VISIT } from "./scripted";

/**
 * The scripted stages carry the product's central safety claim, so they are
 * checked against the *real* predicates rather than against themselves. If
 * `isGated` or `canSpeakTurn` ever changed shape, these fail — which is the
 * point: a canned turn that stopped being gated by the live rule would be a
 * demo that shows something the product no longer does.
 */
describe("scripted scenario", () => {
  it("withholds exactly the dose and the allergy from the patient", () => {
    const gated = SCRIPTED_VISIT.filter(isGated);

    expect(gated.map((turn) => turn.id)).toEqual(["sv4", "sv5"]);
    // The rest reached the patient, so the withholding reads as a decision
    // rather than as the demo simply not working.
    expect(SCRIPTED_VISIT.filter((turn) => !isGated(turn))).toHaveLength(3);
  });

  it("never speaks a gated turn, by the live fail-closed rule", () => {
    for (const turn of SCRIPTED_VISIT.filter(isGated)) {
      expect(canSpeakTurn(turn, false)).toBe(false);
    }
  });

  it("releases a turn only when it is confirmed", () => {
    const before = SCRIPTED_VISIT.find((turn) => turn.id === "sv5")!;
    expect(isGated(before)).toBe(true);

    const after = confirmScripted(SCRIPTED_VISIT, "sv5").find((turn) => turn.id === "sv5")!;
    expect(isGated(after)).toBe(false);
    expect(canSpeakTurn(after, false)).toBe(true);
    expect(spokenText(after)).toContain("Amoxicillin 500 mg");
  });

  it("shows the clinician's correction instead of the machine translation", () => {
    const edited = confirmScripted(SCRIPTED_VISIT, "sv5", "Amoxicillin 500 mg, twice a day").find(
      (turn) => turn.id === "sv5",
    )!;

    expect(edited.status).toBe("corrected");
    expect(spokenText(edited)).toBe("Amoxicillin 500 mg, twice a day");
  });

  it("holds both prescription lines that carry a dose", () => {
    const held = SCRIPTED_DOCUMENT.filter(isGated);

    expect(held).toHaveLength(2);
    for (const turn of held) {
      expect(turn.risk_spans.some((span) => span.kind === "dose_number")).toBe(true);
    }
  });

  // Emma reports a sulfa allergy and is then prescribed amoxicillin, which is
  // safe with that allergy. A script that prescribed a penicillin to a
  // penicillin-allergic patient would put a clinical error on the pitch slide.
  it("stays clinically coherent", () => {
    const allergy = SCRIPTED_VISIT.find((turn) => turn.id === "sv4")!;
    const prescription = SCRIPTED_VISIT.find((turn) => turn.id === "sv5")!;

    expect(allergy.source_text.toLowerCase()).toContain("sulfa");
    expect(prescription.source_text.toLowerCase()).not.toContain("sulfa");
    expect(prescription.source_text.toLowerCase()).not.toContain("penicillin");
  });

  it("is not passed off as live: nothing carries a real session", () => {
    for (const turn of [...SCRIPTED_VISIT, ...SCRIPTED_DOCUMENT]) {
      expect(turn.session_id).toBe("scripted");
    }
  });
});
