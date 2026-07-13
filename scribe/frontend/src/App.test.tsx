import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("language preference", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState(null, "", "/");
    document.documentElement.lang = "vi";
    document.title = "CarePath | Ghi chép bệnh án AI và Phiên dịch khám bệnh trực tiếp";
  });

  it("defaults to Vietnamese and persists a complete English switch", () => {
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(document.title).toBe(
      "CarePath | Ghi chép bệnh án AI và Phiên dịch khám bệnh trực tiếp",
    );
    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(document.documentElement.lang).toBe("en");
    expect(document.title).toBe(
      "CarePath | Clinical note drafting and live medical interpretation",
    );
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
    expect(
      screen.getByRole("link", {
        name: "CarePath Interpreter: Get Interpreter updates",
      }),
    ).toBeInTheDocument();
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
      await screen.findByRole("heading", { name: "Bạn muốn hỗ trợ việc gì hôm nay?" }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
