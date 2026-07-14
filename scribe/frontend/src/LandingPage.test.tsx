import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("renders the Vietnamese Scribe story and a non-interactive Interpreter status", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Tập trung vào người bệnh. Để CarePath soạn bản nháp sau buổi khám.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Một buổi khám không nên biến thành hai ca làm việc.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Một luồng rõ ràng từ tệp âm thanh đến bản nháp.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Bản nháp chỉ được dùng sau khi bác sĩ kiểm tra.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Bắt đầu từ một tệp âm thanh đã được phép sử dụng.",
      }),
    ).toBeInTheDocument();

    const status = document.querySelector<HTMLElement>("[data-interpreter-status]");
    expect(status).toHaveTextContent("Phiên dịch khám bệnh trực tiếp");
    expect(status).toHaveTextContent("Đang phát triển — hiện chưa thể truy cập trên web.");
    expect(status?.querySelector("a, button")).toBeNull();
    expect(
      document.querySelector('a[href*="phien-dich-y-khoa"], a[href*="console"]'),
    ).toBeNull();

    const scribeLinks = screen.getAllByRole("link", { name: "Bắt đầu ghi chép" });
    expect(scribeLinks).toHaveLength(2);
    for (const link of scribeLinks) {
      expect(link).toHaveAttribute("href", "/ghi-chep-lam-sang/");
    }
    expect(document.querySelector(".product-accordion")).toBeNull();
  });

  it("renders equivalent professional English copy", () => {
    render(<LandingPage language="en" />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Focus on the patient. Let CarePath prepare the draft after the visit.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("In development — not currently accessible on the web."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "One consultation should not become two shifts of work.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "The draft is used only after clinician review.",
      }),
    ).toBeInTheDocument();
    for (const link of screen.getAllByRole("link", { name: "Start documenting" })) {
      expect(link).toHaveAttribute("href", "/ghi-chep-lam-sang/");
    }
  });

  it("keeps the landing form scoped to Scribe interest", () => {
    render(<LandingPage language="vi" />);

    expect(screen.getByRole("textbox", { name: "Cơ sở y tế" })).toHaveValue("");
    expect(screen.getByRole("textbox", { name: "Chuyên khoa" })).toHaveValue("");
    expect(screen.queryByRole("combobox", { name: "Chức năng quan tâm" })).not.toBeInTheDocument();
    expect(
      screen.getByText("Biểu mẫu này chỉ dành cho Ghi chép bệnh án AI."),
    ).toBeInTheDocument();
  });
});
