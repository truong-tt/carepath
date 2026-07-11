import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InterpreterConsole } from "./InterpreterConsole";
import type { WsEvent } from "../types";

class FakeWebSocket extends EventTarget {
  static OPEN = 1;
  static instances: FakeWebSocket[] = [];
  readyState = FakeWebSocket.OPEN;

  constructor(public url: string) {
    super();
    FakeWebSocket.instances.push(this);
  }

  send = vi.fn();

  close() {
    this.readyState = 3;
  }

  receive(data: WsEvent) {
    this.dispatchEvent(new MessageEvent("message", { data: JSON.stringify(data) }));
  }
}

afterEach(() => {
  FakeWebSocket.instances = [];
  vi.unstubAllGlobals();
});

describe("InterpreterConsole", () => {
  it("keeps typed turns in their selected doctor and patient regions", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok", provider_mode: "mock" }) }));
    render(<InterpreterConsole sessionId="session-1" />);

    expect(screen.getByRole("heading", { name: "Bác sĩ · Tiếng Việt" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Người bệnh · English" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();

    const input = screen.getByPlaceholderText("Nhập nội dung cần dịch");
    fireEvent.change(input, { target: { value: "xin chào" } });
    fireEvent.submit(input.closest("form")!);
    fireEvent.click(screen.getByRole("button", { name: "Người bệnh · English" }));
    fireEvent.change(screen.getByPlaceholderText("Nhập nội dung cần dịch"), { target: { value: "hello" } });
    fireEvent.submit(screen.getByPlaceholderText("Nhập nội dung cần dịch").closest("form")!);

    expect(FakeWebSocket.instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: "text_turn", speaker: "doctor", lang: "vi", text: "xin chào" }));
    expect(FakeWebSocket.instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: "text_turn", speaker: "patient", lang: "en", text: "hello" }));
  });

  it("selects the patient region from initialSpeaker", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok", provider_mode: "mock" }) }));
    render(<InterpreterConsole initialSpeaker="patient" sessionId="session-1" />);

    expect(screen.getByRole("button", { name: "Người bệnh · English" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Bác sĩ · Tiếng Việt" })).toHaveAttribute("aria-pressed", "false");
  });

  it("renders readback entity text in the confirmation card", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok", provider_mode: "cloud" }),
      }),
    );
    const { rerender } = render(<InterpreterConsole sessionId="session-1" />);
    rerender(<InterpreterConsole language="en" sessionId="session-1" />);

    act(() => {
      FakeWebSocket.instances[0].receive({
        type: "turn_result",
        requires_confirmation: true,
        low_confidence: false,
        turn: {
          id: "turn-1",
          session_id: "session-1",
          seq: 1,
          speaker: "doctor",
          src_lang: "vi",
          tgt_lang: "en",
          source_text: "Uống nửa viên",
          normalized_text: "Uống 0.5 viên",
          translation: "Take half a tablet",
          asr_confidence: 0.99,
          mt_confidence: 0.99,
          risk_tier: "high",
          risk_spans: [],
          readback: {
            back_translation: "Uống nửa viên",
            entities: [
              {
                kind: "dose",
                source_text: "nửa viên",
                translated_text: "half a tablet",
              },
            ],
            flags: [],
          },
          status: "awaiting_confirm",
          corrected_text: null,
          created_at: new Date(0).toISOString(),
        },
      });
    });

    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(screen.getByRole("cell", { name: "Dose" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "nửa viên" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "half a tablet" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Live medical interpretation" })).toBeInTheDocument();
    expect(screen.getByText("Clinician confirmation is required before patient playback.")).toBeInTheDocument();
  });
});
