import { fireEvent, render, screen } from "@testing-library/react";
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
    vi.stubGlobal("AudioContext", class {
      createAnalyser() { return { fftSize: 32, getByteTimeDomainData: (values: Uint8Array) => values.fill(128) }; }
      createMediaStreamSource() { return { connect: vi.fn() }; }
      close = vi.fn();
    });
    vi.stubGlobal("requestAnimationFrame", vi.fn(() => 1));
    vi.stubGlobal("cancelAnimationFrame", vi.fn());
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
});
