import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("language preference", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState(null, "", "/");
    document.documentElement.lang = "vi";
    document.title = "CarePath | Ghi chép bệnh án AI cho bác sĩ Việt Nam";
  });

  it("defaults to Vietnamese and persists a complete English switch", () => {
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(document.title).toBe(
      "CarePath | Ghi chép bệnh án AI cho bác sĩ Việt Nam",
    );
    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(document.documentElement.lang).toBe("en");
    expect(document.title).toBe(
      "CarePath | AI clinical documentation for Vietnamese doctors",
    );
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
    expect(
      screen.getByRole("heading", {
        name: "Focus on the patient. Let CarePath prepare the draft after the visit.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("In development — not currently accessible on the web."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "The draft is used only after clinician review.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("AI assistance, clinician in control."),
    ).toBeInTheDocument();
    expect(
      document.querySelector('a[href*="phien-dich-y-khoa"], a[href*="console"]'),
    ).toBeNull();
  });

  it("ignores an invalid stored preference", () => {
    localStorage.setItem("carepath-demo-language", "fr");
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(
      screen.getByRole("button", { name: "VI" }),
    ).toHaveAttribute("aria-pressed", "true");
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
        name: "Tập trung vào người bệnh. Để CarePath soạn bản nháp sau buổi khám.",
      }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
