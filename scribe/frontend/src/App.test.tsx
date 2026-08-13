import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("public app routing and language", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    window.history.replaceState(null, "", "/");
    document.documentElement.lang = "en";
    document.title = "CarePath";
  });

  it("meets the patient in English and keeps Vietnamese one click away", () => {
    localStorage.setItem("carepath-demo-language", "en");
    render(<App />);

    // The root language follows the audience of the route, not the company:
    // this one is the patient's. See decision 0023.
    expect(document.documentElement.lang).toBe("en");
    // The app no longer writes the title: index.html owns it, so it is correct
    // for a crawler and a link preview before any JS runs. This used to
    // overwrite it from strings.ts with "Bớt gõ bệnh án", the retired
    // Scribe-led product, contradicting the h1 directly below.
    expect(document.title).not.toContain("Bớt gõ bệnh án");
    expect(
      screen.getByRole("heading", {
        name: "Healthcare in Vietnam, without navigating it alone.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Chuyển sang tiếng Việt" }),
    ).toBeInTheDocument();
    expect(
      document.querySelector('a[href*="phien-dich-y-khoa"], a[href*="console"]'),
    ).toBeNull();
  });

  it("serves the care journey and the episode as their own routes", () => {
    window.history.replaceState(null, "", "/get-care/");
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "What do you need help with?" }),
    ).toBeInTheDocument();
    // Neither patient route may reach for the network or the microphone.
    expect(document.querySelector("input[type=file]")).toBeNull();
  });

  it("shows an empty episode rather than an error when there is none", () => {
    window.history.replaceState(null, "", "/my-carepath/");
    render(<App />);

    expect(screen.getByRole("heading", { name: "No care episode yet" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a care journey" })).toHaveAttribute(
      "href",
      "/get-care/",
    );
  });

  it("keeps the clinician's routes Vietnamese", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ asr_ready: true, llm_ready: true }),
      }),
    );
    window.history.replaceState(null, "", "/kham-song-ngu/");
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    vi.unstubAllGlobals();
  });

  it("replaces the legacy #/scribe route with the canonical clinical-note path", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          asr_ready: true,
          llm_ready: true,
          asr_provider: "mock",
          llm_provider: "offline",
        }),
      }),
    );
    window.location.hash = "#/scribe";
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Ghi chép bệnh án AI — bản nháp",
      }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ghi-chep-lam-sang/");
    expect(window.location.hash).toBe("");

    vi.unstubAllGlobals();
  });

  it("follows browser navigation between the landing page and clinical notes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ asr_ready: true, llm_ready: true }),
      }),
    );
    window.history.replaceState(null, "", "/ghi-chep-lam-sang/");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Ghi chép bệnh án AI — bản nháp" }),
    ).toBeInTheDocument();

    window.history.pushState(null, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));

    expect(
      await screen.findByRole("heading", {
        name: "Healthcare in Vietnam, without navigating it alone.",
      }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
