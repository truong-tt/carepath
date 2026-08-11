import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("leads with the foreign patient's problem, not the clinician's typing", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Người bệnh nước ngoài rời phòng khám với tờ giấy họ không đọc được.",
      }),
    ).toBeInTheDocument();
    // The documentation-burden calculator sold the use case the judges rejected.
    expect(screen.queryByRole("spinbutton", { name: /Số người bệnh/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/mỗi ngày/)).not.toBeInTheDocument();
  });

  it("sends the primary action to the bilingual visit", () => {
    render(<LandingPage />);

    const start = screen.getAllByRole("link", { name: "Bắt đầu ca khám" });
    expect(start.length).toBeGreaterThan(0);
    start.forEach((link) => expect(link).toHaveAttribute("href", "/kham-song-ngu/"));
  });

  it("no longer claims the interpreter is unavailable", () => {
    render(<LandingPage />);

    // The banner contradicted the product once the visit screen shipped.
    expect(document.querySelector("[data-interpreter-status]")).toBeNull();
  });

  it("states the harm evidence with its real figures", () => {
    render(<LandingPage />);

    expect(screen.getByText(/49,1%/)).toBeInTheDocument();
    expect(screen.getByText(/29,5%/)).toBeInTheDocument();
    expect(screen.getByText(/52,4%/)).toBeInTheDocument();
    expect(screen.getByText(/22,8 triệu/)).toBeInTheDocument();
  });

  it("keeps the evidence inside its limits", () => {
    render(<LandingPage />);

    expect(
      screen.getByText(/không phải kết quả của CarePath/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Chưa có thử nghiệm lâm sàng/)).toBeInTheDocument();
    expect(screen.getByText(/Chưa đo trên chữ viết tay/)).toBeInTheDocument();
  });

  it("only claims measurements that were actually run", () => {
    render(<LandingPage />);

    // No rounding up: negation is 98% and is stated as 98% on its own row, not
    // folded into the 100% list. An unmeasured metric is not listed at all.
    expect(screen.getByRole("row", { name: /Phủ định\s+98%/ })).toBeInTheDocument();
    expect(screen.queryByText(/chữ viết tay \d+%/)).not.toBeInTheDocument();
    // The measured results are engineering results, and say so.
    expect(screen.getByText(/không phải thử nghiệm lâm sàng/)).toBeInTheDocument();
  });

  it("states the safety boundaries", () => {
    render(<LandingPage />);

    expect(screen.getByText(/Không chẩn đoán, không kê đơn/)).toBeInTheDocument();
    expect(screen.getByText(/Không lưu âm thanh. Không lưu ảnh giấy tờ./)).toBeInTheDocument();
  });

  it("switches the whole page to English for a non-Vietnamese judge", () => {
    render(<LandingPage />);

    fireEvent.click(screen.getByRole("button", { name: "Switch to English" }));

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Foreign patients leave the clinic holding paper they cannot read.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/49.1%/)).toBeInTheDocument();
    expect(screen.getByText(/22.8 million/)).toBeInTheDocument();
  });

  it("shows the Vietnamese document with its English resolved beneath", () => {
    render(<LandingPage />);

    // The pivot's whole claim in one object: Vietnamese paper the patient
    // cannot read, English underneath, and a negation line among them because
    // negation is the metric that is not 100%.
    expect(screen.getByText("Không uống rượu trong thời gian dùng thuốc")).toBeInTheDocument();
    expect(screen.getByText("Do not drink alcohol while taking this medicine")).toBeInTheDocument();
    expect(screen.getByText(/Bác sĩ xác nhận từng dòng/)).toBeInTheDocument();
  });

  it("keeps the pilot form scoped to one interest", () => {
    render(<LandingPage />);

    fireEvent.click(screen.getByText("Dành cho cơ sở muốn thí điểm CarePath"));
    expect(screen.queryByRole("combobox", { name: "Chức năng quan tâm" })).not.toBeInTheDocument();
  });
});
