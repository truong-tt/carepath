import { describe, expect, it } from "vitest";
import { scenarios } from "./scenarios";
import { buildTranscript } from "./transcript";

describe("buildTranscript", () => {
  it("includes the simulation label and both languages", () => {
    const scenario = scenarios[0];
    const transcript = buildTranscript(scenario, scenario.turns.slice(0, 1));

    expect(transcript).toContain("BẢN MÔ PHỎNG");
    expect(transcript).toContain("Chào anh, mời ngồi.");
    expect(transcript).toContain("Hello, please sit down.");
  });
});
