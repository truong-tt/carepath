import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent } from "@testing-library/react";

import { Transcript } from "./Transcript";
import type { TranscriptTurn } from "../types";

const baseTurn: TranscriptTurn = {
  id: "turn-1",
  session_id: "session-1",
  seq: 1,
  speaker: "doctor",
  src_lang: "vi",
  tgt_lang: "en",
  source_text: "uống 500 mg",
  normalized_text: "uống 500 mg",
  translation: "take 500 mg",
  asr_confidence: 1,
  mt_confidence: 0.99,
  risk_tier: "high",
  risk_spans: [],
  readback: null,
  status: "awaiting_confirm",
  corrected_text: null,
  created_at: new Date(0).toISOString(),
  requires_confirmation: true,
};

describe("Transcript", () => {
  it("hides blocked translations until doctor confirmation", () => {
    render(<Transcript turns={[baseTurn]} />);

    expect(screen.getByText("Blocked pending doctor confirmation.")).toBeInTheDocument();
    expect(screen.queryByText("take 500 mg")).not.toBeInTheDocument();
  });

  it("renders non-color risk cues", () => {
    render(
      <Transcript
        turns={[
          {
            ...baseTurn,
            status: "confirmed",
            requires_confirmation: false,
            risk_spans: [
              { start: 0, end: 6, kind: "dose_number", severity: "high", term: "500 mg" },
            ],
          },
        ]}
      />,
    );

    expect(screen.getByText("high: dose_number")).toBeInTheDocument();
    expect(screen.getAllByText("500 mg")).toHaveLength(2);
  });

  it("submits per-turn feedback", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<Transcript turns={[{ ...baseTurn, status: "confirmed", requires_confirmation: false }]} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByRole("button", { name: "Flag translation" }));
    fireEvent.change(screen.getByLabelText("Comment"), { target: { value: "bad term" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit feedback" }));

    expect(await screen.findByText("Feedback saved.")).toBeInTheDocument();
    expect(onFeedback).toHaveBeenCalledWith("turn-1", "wrong_term", "bad term");
  });
});
