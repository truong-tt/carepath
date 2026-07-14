import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ScribeShowcase from "./ScribeShowcase";

describe("ScribeShowcase", () => {
  it("teaches the sample flow without inventing assessment or plan", () => {
    render(<ScribeShowcase />);

    expect(screen.getByText(/Tôi bị đau tức ngực thoáng qua/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "2. Nội dung được làm rõ" }));
    expect(screen.getByText("Chưa có kết quả điện tâm đồ")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "3. Bản nháp có cấu trúc" }));
    expect(screen.getAllByText("Chờ bác sĩ nhập hoặc xác nhận.")).toHaveLength(2);
    expect(screen.getByText("Nhận định")).toBeInTheDocument();
    expect(screen.getByText("Kế hoạch")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "4. Bác sĩ kiểm tra" }));
    expect(screen.getByText("Trước khi sử dụng bản nháp")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Mở công cụ và tải tệp âm thanh" }),
    ).toHaveAttribute("href", "/ghi-chep-lam-sang/");
  });
});
