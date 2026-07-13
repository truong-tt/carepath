import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeviceCheck } from "./DeviceCheck";

afterEach(() => vi.unstubAllGlobals());

function installMedia(stream?: MediaStream) {
  const getUserMedia = vi.fn().mockResolvedValue(stream);
  vi.stubGlobal("navigator", {
    mediaDevices: {
      enumerateDevices: vi.fn().mockResolvedValue([{ deviceId: "mic-1", kind: "audioinput", label: "Clinic mic" }]),
      getUserMedia,
    },
  });
  return getUserMedia;
}

function installAudio() {
  vi.stubGlobal("AudioContext", class {
    createAnalyser() { return { fftSize: 32, getByteTimeDomainData: (values: Uint8Array) => values.fill(128) }; }
    createMediaStreamSource() { return { connect: vi.fn() }; }
    close = vi.fn();
  });
  vi.stubGlobal("requestAnimationFrame", vi.fn(() => 1));
  vi.stubGlobal("cancelAnimationFrame", vi.fn());
}

describe("DeviceCheck", () => {
  it("does not request a microphone before the clinician starts a test", async () => {
    const getUserMedia = installMedia();
    render(<DeviceCheck onComplete={vi.fn()} />);

    await screen.findByRole("button", { name: "Kiểm tra micrô" });
    expect(getUserMedia).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục bằng văn bản" }));
    expect(getUserMedia).not.toHaveBeenCalled();
  });

  it("stops the test stream when continuing with typed turns", async () => {
    const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
    const getUserMedia = installMedia({ getTracks: () => [track] } as MediaStream);
    installAudio();
    const onComplete = vi.fn();
    render(<DeviceCheck onComplete={onComplete} />);

    await screen.findByRole("button", { name: "Kiểm tra micrô" });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra micrô" }));
    await screen.findByText("Micrô đã sẵn sàng.");
    expect(getUserMedia).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục bằng văn bản" }));

    expect(track.stop).toHaveBeenCalled();
    expect(onComplete).toHaveBeenCalledWith({ voiceReady: false });
  });

  it("stops the test stream when continuing with voice", async () => {
    const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
    installMedia({ getTracks: () => [track] } as MediaStream);
    installAudio();
    const onComplete = vi.fn();
    render(<DeviceCheck onComplete={onComplete} />);

    await screen.findByRole("button", { name: "Kiểm tra micrô" });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra micrô" }));
    await screen.findByText("Micrô đã sẵn sàng.");
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục bằng micrô" }));

    expect(track.stop).toHaveBeenCalled();
    expect(onComplete).toHaveBeenCalledWith({ deviceId: "mic-1", voiceReady: true });
  });

  it("stops the test stream on unmount", async () => {
    const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
    installMedia({ getTracks: () => [track] } as MediaStream);
    installAudio();
    const { unmount } = render(<DeviceCheck onComplete={vi.fn()} />);

    await screen.findByRole("button", { name: "Kiểm tra micrô" });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra micrô" }));
    await screen.findByText("Micrô đã sẵn sàng.");
    unmount();

    expect(track.stop).toHaveBeenCalled();
  });

  it("stops a stream that resolves after unmount", async () => {
    const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
    let resolveStream!: (stream: MediaStream) => void;
    const getUserMedia = vi.fn(() => new Promise<MediaStream>((resolve) => { resolveStream = resolve; }));
    vi.stubGlobal("navigator", {
      mediaDevices: {
        enumerateDevices: vi.fn().mockResolvedValue([{ deviceId: "mic-1", kind: "audioinput", label: "Clinic mic" }]),
        getUserMedia,
      },
    });
    const { unmount } = render(<DeviceCheck onComplete={vi.fn()} />);

    await screen.findByRole("button", { name: "Kiểm tra micrô" });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra micrô" }));
    expect(getUserMedia).toHaveBeenCalledOnce();
    unmount();
    await act(async () => resolveStream({ getTracks: () => [track] } as MediaStream));

    expect(track.stop).toHaveBeenCalled();
  });
});
