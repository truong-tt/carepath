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
  it("renders the complete English empty state", () => {
    render(<Transcript language="en" turns={[]} />);

    expect(screen.getByRole("heading", { name: "Conversation" })).toBeInTheDocument();
    expect(screen.getByText("No turns yet.")).toBeInTheDocument();
  });

  it("hides blocked translations until doctor confirmation", () => {
    render(<Transcript turns={[baseTurn]} />);

    expect(screen.getByText("Đã chặn, chờ bác sĩ xác nhận.")).toBeInTheDocument();
    expect(screen.queryByText("take 500 mg")).not.toBeInTheDocument();
  });

  it("keeps low-confidence recovery actions on their affected turns", () => {
    const onRepeat = vi.fn();
    const onType = vi.fn();
    render(<Transcript turns={[{ ...baseTurn, id: "low-1", low_confidence: true, requires_confirmation: false, status: "delivered" }, { ...baseTurn, id: "low-2", low_confidence: true, requires_confirmation: false, status: "delivered" }]} onRepeat={onRepeat} onType={onType} />);

    expect(screen.getAllByRole("alert")).toHaveLength(2);
    fireEvent.click(screen.getAllByRole("button", { name: "Nói lại" })[1]);
    fireEvent.click(screen.getAllByRole("button", { name: "Nhập văn bản" })[0]);
    expect(onRepeat).toHaveBeenCalledWith(expect.objectContaining({ id: "low-2" }));
    expect(onType).toHaveBeenCalledWith(expect.objectContaining({ id: "low-1" }));
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

    expect(screen.getByText("Cao: Liều lượng")).toBeInTheDocument();
    expect(screen.getAllByText("500 mg")).toHaveLength(2);
  });

  it("submits per-turn feedback", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<Transcript turns={[{ ...baseTurn, status: "confirmed", requires_confirmation: false }]} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByRole("button", { name: "Báo lỗi bản dịch" }));
    fireEvent.change(screen.getByLabelText("Ghi chú"), { target: { value: "bad term" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi phản hồi" }));

    expect(await screen.findByText("Đã lưu phản hồi.")).toBeInTheDocument();
    expect(onFeedback).toHaveBeenCalledWith("turn-1", "wrong_term", "bad term");
  });
});
