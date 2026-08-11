import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hasVoiceFor, speak } from "./speech";

const playMock = vi.fn(() => Promise.resolve());
const speakMock = vi.fn();

beforeEach(() => {
  playMock.mockClear();
  speakMock.mockClear();
  vi.stubGlobal("speechSynthesis", {
    speak: speakMock,
    cancel: vi.fn(),
    getVoices: () => [{ lang: "en-US", name: "English" }],
  });
  vi.stubGlobal("SpeechSynthesisUtterance", class {
    lang = "";
    constructor(public text: string) {}
  });
  vi.stubGlobal("Audio", class {
    onended: (() => void) | null = null;
    constructor(public src: string) {}
    play = playMock;
    pause = vi.fn();
  });
  vi.stubGlobal("URL", {
    createObjectURL: () => "blob:fake",
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => vi.unstubAllGlobals());

describe("hasVoiceFor", () => {
  it("reports the missing Vietnamese voice that motivates server TTS", () => {
    expect(hasVoiceFor("vi")).toBe(false);
    expect(hasVoiceFor("en")).toBe(true);
  });
});

describe("speak", () => {
  it("uses the browser directly for English", async () => {
    vi.stubGlobal("fetch", vi.fn());

    await speak("Take one tablet", "en");

    expect(speakMock).toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("routes Vietnamese through the server voice", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, blob: async () => new Blob(["wav"]) }));
    vi.stubGlobal("fetch", fetchMock);

    await speak("Tôi uống 500 mg", "vi");

    expect(fetchMock).toHaveBeenCalled();
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain("/api/v1/speech");
    expect(JSON.parse(init.body as string)).toEqual({ text: "Tôi uống 500 mg", lang: "vi" });
    expect(playMock).toHaveBeenCalled();
    expect(speakMock).not.toHaveBeenCalled();
  });

  it("falls back to the browser when the server voice is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 })));

    await speak("Tôi uống 500 mg", "vi");

    // Degraded audio beats a silent consultation.
    expect(speakMock).toHaveBeenCalled();
    expect(playMock).not.toHaveBeenCalled();
  });

  it("falls back when the network throws", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new Error("offline"); }));

    await speak("Tôi uống 500 mg", "vi");

    expect(speakMock).toHaveBeenCalled();
  });
});
