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
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Choose the right product for the right point in care.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "One shared oversight layer. Two product-specific safety systems.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Turn what was said into a structured draft.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "See how each product keeps review points in the right place.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Choose the product that fits your workflow.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("AI assistance, clinician in control."),
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
        name: "Ghi chép bệnh án AI",
      }),
    ).toBeInTheDocument();

    window.location.hash = "";
    vi.unstubAllGlobals();
  });
});
