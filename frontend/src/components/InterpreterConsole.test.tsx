import { act, render, screen } from "@testing-library/react";
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
  it("renders readback entity text in the confirmation card", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok", provider_mode: "cloud" }),
      }),
    );
    render(<InterpreterConsole sessionId="session-1" />);

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

    expect(screen.getByRole("cell", { name: "Liều lượng" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "nửa viên" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "half a tablet" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
  });
});
