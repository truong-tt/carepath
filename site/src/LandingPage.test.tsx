import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("renders the Vietnamese evidence-led page", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("heading", {
        name: /Phiên dịch y khoa, xác nhận trước khi phát/,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Bản dịch quan trọng không được tự động đi thẳng tới người bệnh.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("TODO-pricing")).toBeInTheDocument();
  });

  it("renders the complete page in English", () => {
    render(<LandingPage language="en" />);

    expect(
      screen.getByRole("heading", {
        name: /Clinical translation, confirmed before delivery/,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Important translations do not automatically pass straight to the patient.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Status-quo costs need honest context.",
      }),
    ).toBeInTheDocument();
  });
});
