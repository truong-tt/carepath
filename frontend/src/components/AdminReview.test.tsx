import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AdminReview } from "./AdminReview";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("AdminReview", () => {
  it("shows a 401 error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
      }),
    );
    render(<AdminReview />);

    fireEvent.change(screen.getByLabelText("Admin token"), { target: { value: "bad" } });
    fireEvent.click(screen.getByRole("button", { name: "Load review" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("401");
  });

  it("renders rows from the review endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        total: 1,
        items: [
          {
            id: "turn-1",
            source_text: "uống 500 mg",
            translation: "take 500 mg",
            corrected_text: "take 500 mg after food",
            risk_tier: "high",
            status: "corrected",
            feedback: [{ reason: "wrong_term" }],
          },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<AdminReview />);

    fireEvent.change(screen.getByLabelText("Admin token"), { target: { value: "secret" } });
    fireEvent.change(screen.getByLabelText("Risk"), { target: { value: "high" } });
    fireEvent.click(screen.getByLabelText("Flagged"));
    fireEvent.click(screen.getByRole("button", { name: "Load review" }));

    expect(await screen.findByText("uống 500 mg")).toBeInTheDocument();
    expect(screen.getByText("take 500 mg")).toBeInTheDocument();
    expect(screen.getByText("take 500 mg after food")).toBeInTheDocument();
    expect(screen.getByText("wrong_term")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toContain("risk=high");
    expect(fetchMock.mock.calls[0][0]).toContain("flagged=1");
    expect(fetchMock.mock.calls[0][1]).toEqual({ headers: { "X-Admin-Token": "secret" } });
  });
});
