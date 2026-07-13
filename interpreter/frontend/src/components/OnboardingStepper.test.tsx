import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OnboardingStepper } from "./OnboardingStepper";

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("OnboardingStepper", () => {
  it("shows five text-labeled steps and keeps consent current until submitted", () => {
    localStorage.setItem("carepath-demo-language", "vi");
    localStorage.setItem("carepath-onboarding-role", "doctor");
    localStorage.setItem("carepath-onboarding-direction", "vi-en");
    const { rerender } = render(<OnboardingStepper consentSubmitted={false} language="vi" />);

    expect(screen.getAllByRole("listitem")).toHaveLength(5);
    expect(screen.getByText("Xác nhận").closest("li")).toHaveAttribute("aria-current", "step");
    expect(screen.getByText("Xác nhận").closest("li")).toHaveTextContent("Đang thực hiện");

    rerender(<OnboardingStepper consentSubmitted language="vi" />);
    expect(screen.getByText("Xác nhận").closest("li")).toHaveTextContent("Đã hoàn thành");
    expect(screen.getByText("Kiểm tra thiết bị").closest("li")).toHaveAttribute("aria-current", "step");
  });
});
