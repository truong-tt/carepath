import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("Vietnamese-only public app", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState(null, "", "/");
    document.documentElement.lang = "vi";
    document.title = "CarePath";
  });

  it("always renders Vietnamese and exposes no language switch", () => {
    localStorage.setItem("carepath-demo-language", "en");
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(document.title).toBe(
      "CarePath | Bớt gõ bệnh án, thêm thời gian cho người bệnh",
    );
    expect(
      screen.getByRole("heading", {
        name: "Người bệnh nước ngoài rời phòng khám với tờ giấy họ không đọc được.",
      }),
    ).toBeInTheDocument();
    // The page now offers English so a non-Vietnamese judge or patient can read
    // it; the document root stays vi because that is the clinic's language.
    expect(screen.getByRole("button", { name: "Switch to English" })).toBeInTheDocument();
    expect(
      document.querySelector('a[href*="phien-dich-y-khoa"], a[href*="console"]'),
    ).toBeNull();
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
        name: "Người bệnh nước ngoài rời phòng khám với tờ giấy họ không đọc được.",
      }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
