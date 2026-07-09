import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("CarePath Translate scaffold", () => {
  it("renders the brand and simulation disclosure", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Translate" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Bản mô phỏng — không phải bản dịch trực tiếp"),
    ).toBeInTheDocument();
  });
});
