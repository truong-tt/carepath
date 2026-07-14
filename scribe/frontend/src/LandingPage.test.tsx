import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage, { formatMinutes } from "./LandingPage";

describe("LandingPage", () => {
  it("leads with the doctor's problem and keeps Interpreter unavailable", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Trải nghiệm ca khám mẫu" }),
    ).toHaveAttribute("href", "#demo");
    expect(
      screen.getByRole("link", { name: "Tính thời gian ghi chép" }),
    ).toHaveAttribute("href", "#calculator");
    expect(screen.queryByRole("button", { name: "EN" })).not.toBeInTheDocument();

    const status = document.querySelector<HTMLElement>("[data-interpreter-status]");
    expect(status).toHaveTextContent("Phiên dịch khám bệnh trực tiếp");
    expect(status).toHaveTextContent("Đang phát triển — hiện chưa thể truy cập trên web.");
    expect(status?.querySelector("a, button")).toBeNull();
    expect(
      document.querySelector('a[href*="phien-dich-y-khoa"], a[href*="console"]'),
    ).toBeNull();
  });

  it("shows the conversation-to-draft proof without inventing assessment or plan", () => {
    render(<LandingPage />);

    expect(screen.getByText("Từ cuộc trao đổi đến bản nháp")).toBeInTheDocument();
    expect(
      screen.getByText("Chưa có kết quả cận lâm sàng trong nội dung ghi âm."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Nhận định và kế hoạch luôn thuộc về bác sĩ/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Chờ bác sĩ nhập hoặc xác nhận.")).not.toBeInTheDocument();
  });

  it("calculates current documentation time without claiming CarePath savings", () => {
    render(<LandingPage />);

    fireEvent.change(screen.getByRole("spinbutton", { name: "Số người bệnh mỗi ngày" }), {
      target: { value: "28" },
    });
    fireEvent.change(
      screen.getByRole("spinbutton", { name: "Phút ghi chép cho mỗi người bệnh" }),
      { target: { value: "5" } },
    );

    expect(screen.getByText("2 giờ 20 phút mỗi ngày")).toBeInTheDocument();
    expect(screen.getByText("11 giờ 40 phút cho 5 ngày làm việc")).toBeInTheDocument();
    expect(screen.getByText(/Công thức: 28 người bệnh × 5 phút/)).toBeInTheDocument();
    expect(screen.queryByText(/CarePath tiết kiệm/i)).not.toBeInTheDocument();
  });

  it("keeps the pilot form scoped to Scribe interest", () => {
    render(<LandingPage />);

    fireEvent.click(screen.getByText("Dành cho cơ sở muốn thí điểm CarePath"));
    expect(screen.getByRole("textbox", { name: "Cơ sở y tế" })).toHaveValue("");
    expect(screen.queryByRole("combobox", { name: "Chức năng quan tâm" })).not.toBeInTheDocument();
    expect(
      screen.getByText(/Biểu mẫu này chỉ dành cho Ghi chép bệnh án AI/),
    ).toBeInTheDocument();
  });
});

describe("formatMinutes", () => {
  it("formats whole hours and remaining minutes", () => {
    expect(formatMinutes(140)).toBe("2 giờ 20 phút");
    expect(formatMinutes(120)).toBe("2 giờ");
    expect(formatMinutes(45)).toBe("45 phút");
  });
});
