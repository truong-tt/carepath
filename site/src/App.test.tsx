import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("language preference", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = "vi";
  });

  it("defaults to Vietnamese and persists a complete English switch", () => {
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(document.documentElement.lang).toBe("en");
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
    expect(
      screen.getByRole("heading", {
        name: /Medical interpreting and notes, confirmed before use/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "A misunderstood sentence can travel beyond one conversation.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Important content does not pass straight to the patient or the record.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "From spoken visit to a SOAP draft.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Speak. Review. Deliver only after confirmation.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Status-quo costs need honest context.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Keep the demo you just created",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("AI assistance, clinician confirmed."),
    ).toBeInTheDocument();
  });

  it("ignores an invalid stored preference", () => {
    localStorage.setItem("carepath-demo-language", "fr");
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(
      screen.getByRole("button", { name: "VI" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("routes #/scribe to the Scribe tool page", async () => {
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
        name: "Từ bản ghi âm buổi khám đến bệnh án SOAP",
      }),
    ).toBeInTheDocument();

    window.location.hash = "";
    vi.unstubAllGlobals();
  });
});
