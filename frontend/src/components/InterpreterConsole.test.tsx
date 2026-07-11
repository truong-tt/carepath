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

  open() {
    this.dispatchEvent(new Event("open"));
  }

  receive(data: WsEvent) {
    this.dispatchEvent(new MessageEvent("message", { data: JSON.stringify(data) }));
  }
}

class FakeMediaRecorder extends EventTarget {
  state: RecordingState = "inactive";

  constructor() {
    super();
  }

  start = vi.fn(() => {
    this.state = "recording";
  });

  stop = vi.fn(() => {
    this.state = "inactive";
    this.dispatchEvent(new Event("stop"));
  });
}

afterEach(() => {
  FakeWebSocket.instances = [];
  vi.unstubAllGlobals();
});

function openSocket() {
  act(() => FakeWebSocket.instances[0].open());
}

describe("InterpreterConsole", () => {
  it("keeps typed turns in their selected doctor and patient regions", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok", provider_mode: "mock" }) }));
    render(<InterpreterConsole sessionId="session-1" />);
    openSocket();

    expect(screen.getByRole("heading", { name: "Bác sĩ · Tiếng Việt" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Người bệnh · English" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();

    const input = screen.getByPlaceholderText("Nhập nội dung cần dịch");
    fireEvent.change(input, { target: { value: "xin chào" } });
    fireEvent.submit(input.closest("form")!);
    act(() => FakeWebSocket.instances[0].receive({ type: "turn_error", message: "retry", retryable: true }));
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

  it("prevents overlapping starts while microphone permission is pending", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok", provider_mode: "mock" }) }));
    const getUserMedia = vi.fn(() => new Promise<MediaStream>(() => undefined));
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
    vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
    render(<InterpreterConsole sessionId="session-1" />);
    openSocket();

    const talk = screen.getByRole("button", { name: "Nhấn giữ để nói" });
    fireEvent.keyDown(talk, { key: "Enter" });
    fireEvent.keyDown(talk, { key: "Enter" });

    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(talk).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("uses Space push-to-talk and releases microphone tracks", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok", provider_mode: "mock" }) }));
    const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [track] }) } });
    vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
    render(<InterpreterConsole sessionId="session-1" />);
    openSocket();

    const talk = screen.getByRole("button", { name: "Nhấn giữ để nói" });
    fireEvent.keyDown(talk, { key: " " });
    await act(async () => undefined);
    expect(talk).toHaveAttribute("aria-pressed", "true");
    fireEvent.keyUp(talk, { key: " " });

    expect(track.stop).toHaveBeenCalled();
    expect(FakeWebSocket.instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: "start_turn", speaker: "doctor", lang: "vi" }));
    expect(FakeWebSocket.instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: "end_turn" }));
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
    expect(screen.queryByText("Take half a tablet")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open review" }));
    expect(screen.getByLabelText("Clinician confirmation 1")).toHaveFocus();
    expect(screen.getByRole("cell", { name: "Dose" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "nửa viên" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "half a tablet" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Live medical interpretation" })).toBeInTheDocument();
    expect(screen.getByText("Clinician confirmation is required before patient playback.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm and play" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Edit translation"), { target: { value: "" } });
    expect(screen.getByRole("button", { name: "Save edit and play" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Edit translation"), { target: { value: "Take one half" } });
    expect(screen.getByRole("button", { name: "Save edit and play" })).toBeEnabled();
  });
});
