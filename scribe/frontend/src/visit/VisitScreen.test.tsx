import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { canSpeakTurn, isGated, type VisitTurn } from "./types";
import { riskLabel, RISK_LABELS } from "./riskLabels";

const socketState = vi.hoisted(() => ({
  turns: [] as VisitTurn[],
  sendTurn: vi.fn(),
  replaceTurn: vi.fn(),
  addTurns: vi.fn(),
  setOnTurn: vi.fn(),
  clearError: vi.fn(),
  connection: "open" as const,
  error: null as { message: string; retryable: boolean } | null,
  pending: false,
}));

const confirmTurnMock = vi.hoisted(() => vi.fn());
const finishVisitMock = vi.hoisted(() => vi.fn());

vi.mock("./useVisitSocket", () => ({
  useVisitSocket: () => socketState,
  startVisit: vi.fn(async () => "visit-1"),
  confirmTurn: confirmTurnMock,
  escalateVisit: vi.fn(async () => undefined),
  finishVisit: finishVisitMock,
}));

const speakMock = vi.hoisted(() => vi.fn());
vi.mock("./speech", () => ({
  speak: speakMock,
  cancelSpeech: vi.fn(),
  speechSupported: () => true,
  listenOnce: vi.fn(() => ({ stop: vi.fn(), abort: vi.fn() })),
  BCP47: { vi: "vi-VN", en: "en-US" },
}));

import VisitScreen from "./VisitScreen";

function turn(overrides: Partial<VisitTurn> = {}): VisitTurn {
  return {
    id: "t1",
    session_id: "visit-1",
    seq: 1,
    speaker: "patient",
    src_lang: "en",
    tgt_lang: "vi",
    source_text: "I take 15 milligrams",
    normalized_text: "I take 15 mg",
    translation: "Tôi uống 15 mg",
    asr_confidence: 0.42,
    mt_confidence: 0.95,
    risk_tier: "high",
    risk_spans: [
      { kind: "dose_number", severity: "high", term: "15 mg" },
      { kind: "low_confidence", severity: "low", term: "confidence" },
    ],
    readback: {
      back_translation: "I take fifteen milligrams",
      entities: [],
      flags: ["dose_uncertain"],
    },
    status: "awaiting_confirm",
    corrected_text: null,
    created_at: new Date().toISOString(),
    requires_confirmation: true,
    low_confidence: true,
    ...overrides,
  };
}

async function startVisit() {
  render(<VisitScreen />);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: /Bắt đầu khám/ }));
  await screen.findByRole("heading", { name: /Khám bệnh nhân nước ngoài/ });
}

beforeEach(() => {
  window.sessionStorage.clear();
  socketState.turns = [];
  socketState.error = null;
  socketState.pending = false;
  speakMock.mockClear();
  confirmTurnMock.mockReset();
  finishVisitMock.mockReset();
});

afterEach(() => vi.clearAllMocks());

describe("fail-closed playback", () => {
  it("refuses to speak a turn awaiting confirmation", () => {
    expect(canSpeakTurn(turn(), false)).toBe(false);
  });

  it("refuses to speak a blocked turn even if flags were cleared", () => {
    const blocked = turn({
      status: "blocked",
      requires_confirmation: false,
      low_confidence: false,
    });
    expect(canSpeakTurn(blocked, false)).toBe(false);
  });

  it("refuses to speak a low-confidence turn", () => {
    const delivered = turn({
      status: "delivered",
      requires_confirmation: false,
      low_confidence: true,
    });
    expect(canSpeakTurn(delivered, false)).toBe(false);
  });

  it("speaks a confirmed turn", () => {
    const confirmed = turn({
      status: "confirmed",
      requires_confirmation: false,
      low_confidence: false,
    });
    expect(canSpeakTurn(confirmed, false)).toBe(true);
  });

  it("stays silent once a human interpreter has been requested", () => {
    const confirmed = turn({
      status: "confirmed",
      requires_confirmation: false,
      low_confidence: false,
    });
    expect(canSpeakTurn(confirmed, true)).toBe(false);
  });
});

describe("gated turns in the UI", () => {
  it("masks the translation and never shows it to the patient", async () => {
    socketState.turns = [turn()];
    await startVisit();

    expect(isGated(socketState.turns[0])).toBe(true);
    expect(screen.getAllByText(/Đang chờ bác sĩ xác nhận/).length).toBeGreaterThan(0);
    // The clinician's gate card shows the draft; the patient column must not.
    const columns = screen.getByLabelText("Bệnh nhân");
    expect(columns.textContent).not.toContain("Tôi uống 15 mg");
  });

  it("shows the back-translation and the confidence the clinician needs", async () => {
    socketState.turns = [turn()];
    await startVisit();

    expect(screen.getByText("I take fifteen milligrams")).toBeInTheDocument();
    expect(screen.getByText(/Bệnh nhân chưa nghe/)).toBeInTheDocument();
    // Rendered as separate text nodes, so assert against the card as a whole.
    const gate = screen.getByText(/Cần bác sĩ xác nhận/).closest("article");
    expect(gate?.textContent).toContain("42%");
    expect(gate?.textContent).toContain("I take 15 milligrams");
  });

  it("attributes the gated turn to whoever actually said it", async () => {
    // Doses come from the doctor, so a gate card hardcoded to "Bệnh nhân nói"
    // was wrong on the case it exists for.
    socketState.turns = [turn({ speaker: "doctor", src_lang: "vi", tgt_lang: "en" })];
    await startVisit();

    const gate = screen.getByText(/Cần bác sĩ xác nhận/).closest("article");
    expect(gate?.textContent).toContain("Bác sĩ nói");
    expect(gate?.textContent).not.toContain("Bệnh nhân nói");
  });

  it("does not speak while the turn is gated", async () => {
    socketState.turns = [turn()];
    await startVisit();
    expect(speakMock).not.toHaveBeenCalled();
  });

  it("speaks only after the clinician confirms", async () => {
    socketState.turns = [turn()];
    confirmTurnMock.mockResolvedValue({
      ...turn(),
      status: "confirmed",
      corrected_text: null,
    });
    await startVisit();

    fireEvent.click(screen.getByRole("button", { name: /Xác nhận và đọc/ }));

    await waitFor(() => expect(speakMock).toHaveBeenCalledWith("Tôi uống 15 mg", "vi"));
  });

  it("sends the clinician's edit instead of the machine translation", async () => {
    socketState.turns = [turn()];
    confirmTurnMock.mockResolvedValue({
      ...turn(),
      status: "corrected",
      corrected_text: "Tôi uống 500 mg",
    });
    await startVisit();

    fireEvent.click(screen.getByRole("button", { name: "Sửa" }));
    fireEvent.change(screen.getByLabelText("Sửa bản dịch"), {
      target: { value: "Tôi uống 500 mg" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Lưu bản sửa/ }));

    await waitFor(() => expect(confirmTurnMock).toHaveBeenCalledWith("t1", "Tôi uống 500 mg"));
    await waitFor(() => expect(speakMock).toHaveBeenCalledWith("Tôi uống 500 mg", "vi"));
  });

  it("keeps the turn gated when confirmation fails", async () => {
    socketState.turns = [turn()];
    confirmTurnMock.mockRejectedValue(new Error("network"));
    await startVisit();

    fireEvent.click(screen.getByRole("button", { name: /Xác nhận và đọc/ }));

    await screen.findByText(/vẫn chưa gửi cho bệnh nhân/);
    expect(speakMock).not.toHaveBeenCalled();
  });
});

describe("entity chips", () => {
  it("renders a specific label for each medical entity", async () => {
    socketState.turns = [
      turn({
        status: "delivered",
        requires_confirmation: false,
        low_confidence: false,
        risk_tier: "medium",
        risk_spans: [
          { kind: "drug_name", severity: "high", term: "amoxicillin" },
          { kind: "dose_number", severity: "high", term: "500 mg" },
          { kind: "allergy", severity: "critical", term: "dị ứng" },
        ],
      }),
    ];
    await startVisit();

    expect(screen.getByText("Tên thuốc")).toBeInTheDocument();
    expect(screen.getByText("Liều dùng")).toBeInTheDocument();
    expect(screen.getByText("Dị ứng thuốc")).toBeInTheDocument();
    expect(screen.getByText("amoxicillin")).toBeInTheDocument();
  });

  it("drops stale chips once the clinician has rewritten the translation", async () => {
    socketState.turns = [
      turn({
        status: "corrected",
        corrected_text: "Tôi uống 500 mg",
        requires_confirmation: false,
        low_confidence: false,
        risk_spans: [{ kind: "dose_number", severity: "high", term: "15 mg" }],
      }),
    ];
    await startVisit();

    // The chip described the superseded draft; showing "15 mg" under a
    // translation the clinician changed to 500 mg would contradict it.
    expect(screen.getByText("Tôi uống 500 mg")).toBeInTheDocument();
    expect(screen.queryByText("15 mg")).not.toBeInTheDocument();
    expect(screen.queryByText("Liều dùng")).not.toBeInTheDocument();
  });

  it("never renders the generic fallback for a known kind", () => {
    for (const kind of Object.keys(RISK_LABELS)) {
      expect(riskLabel(kind).vi).not.toBe("Thông tin cần kiểm tra");
    }
  });

  it("falls back safely for an unknown kind", () => {
    expect(riskLabel("brand_new_detector").vi).toBe("Thông tin cần kiểm tra");
  });
});

describe("document capture", () => {
  function pickFile(name = "donthuoc.png") {
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!;
    const file = new File(["x"], name, { type: "image/png" });
    Object.defineProperty(input, "files", { value: [file], configurable: true });
    fireEvent.change(input);
    return input;
  }

  it("opens the camera on a touch device", async () => {
    await startVisit();
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!;

    expect(input).toBeTruthy();
    expect(input.getAttribute("accept")).toBe("image/*");
    // capture=environment is what makes a tablet open the rear camera directly.
    expect(input.getAttribute("capture")).toBe("environment");
  });

  it("adds the lines it read as turns", async () => {
    const documentTurn = turn({
      id: "doc1",
      speaker: "document",
      src_lang: "vi",
      tgt_lang: "en",
      source_text: "Amoxicillin 500 mg Uống 1 viên, ngày 2 lần",
      translation: "Amoxicillin 500 mg - take 1 tablet, 2 times a day",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: true, json: async () => [documentTurn] })),
    );
    await startVisit();

    pickFile();

    await waitFor(() => expect(socketState.addTurns).toHaveBeenCalledWith([documentTurn]));
    expect(await screen.findByText(/Đã đọc 1 dòng/)).toBeInTheDocument();
  });

  it("states the recovery and adds nothing when the read fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 502 })));
    await startVisit();

    pickFile();

    expect(await screen.findByText(/Không đọc được giấy tờ/)).toBeInTheDocument();
    expect(socketState.addTurns).not.toHaveBeenCalled();
  });

  it("distinguishes an unreadable photo from a failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, json: async () => [] })));
    await startVisit();

    pickFile();

    // Fail-closed on the backend means zero lines, not invented ones. Say so.
    expect(await screen.findByText(/Không đọc được chữ nào/)).toBeInTheDocument();
    expect(socketState.addTurns).not.toHaveBeenCalled();
  });

  it("shows a busy state while reading", async () => {
    let release: (value: unknown) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise((resolve) => (release = resolve))),
    );
    await startVisit();

    pickFile();

    expect(await screen.findByText("Đang đọc giấy tờ…")).toBeInTheDocument();
    release({ ok: true, json: async () => [] });
  });
});

describe("surviving a refresh", () => {
  it("resumes the visit instead of showing the start form again", async () => {
    window.sessionStorage.setItem("carepath.visitId", "visit-existing");

    render(<VisitScreen />);

    // Straight into the consultation: no consent form, no lost transcript.
    expect(await screen.findByLabelText("Bệnh nhân")).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("remembers the visit once it starts", async () => {
    await startVisit();
    expect(window.sessionStorage.getItem("carepath.visitId")).toBe("visit-1");
  });
});

describe("typed fallback", () => {
  it("submits a typed turn without a confidence value", async () => {
    await startVisit();

    fireEvent.change(screen.getByLabelText("Gõ tiếng Việt"), {
      target: { value: "Ngừng thuốc này" },
    });
    fireEvent.submit(screen.getByLabelText("Gõ tiếng Việt").closest("form")!);

    // No confidence argument: a typed turn carries no recognition uncertainty,
    // and the server defaults an absent value to fully confident.
    expect(socketState.sendTurn).toHaveBeenCalledWith("doctor", "vi", "Ngừng thuốc này");
  });
});
