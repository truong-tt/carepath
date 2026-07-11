import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { IntentQuiz } from "./IntentQuiz";

describe("IntentQuiz", () => {
  it("uses recommended defaults and persists the two answers", () => {
    localStorage.clear();
    const onComplete = vi.fn();
    render(<IntentQuiz language="vi" onComplete={onComplete} />);

    expect(screen.getByLabelText("Bác sĩ")).toBeChecked();
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục" }));
    expect(screen.getByLabelText("Tiếng Việt → Tiếng Anh")).toBeChecked();
    fireEvent.click(screen.getByLabelText("Tiếng Anh → Tiếng Việt"));
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục" }));

    expect(onComplete).toHaveBeenCalledWith({ role: "doctor", direction: "en-vi" });
    expect(localStorage.getItem("carepath-onboarding-role")).toBe("doctor");
    expect(localStorage.getItem("carepath-onboarding-direction")).toBe("en-vi");
  });

  it("prefills stored choices and lets users skip", () => {
    localStorage.setItem("carepath-onboarding-role", "clinic_staff");
    localStorage.setItem("carepath-onboarding-direction", "en-vi");
    const onComplete = vi.fn();
    render(<IntentQuiz language="vi" onComplete={onComplete} />);

    expect(screen.getByLabelText("Nhân viên phòng khám")).toBeChecked();
    fireEvent.click(screen.getByRole("button", { name: "Bỏ qua và dùng lựa chọn đề xuất" }));
    expect(onComplete).toHaveBeenCalledWith({ role: "doctor", direction: "vi-en" });
  });
});
