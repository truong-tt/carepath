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
    expect(screen.getByText(/21,2 triệu/)).toBeInTheDocument();
    expect(screen.getByText(/161\.992 lao động nước ngoài/)).toBeInTheDocument();
  });

  it("credits the comparison to the study it comes from", () => {
    render(<LandingPage />);

    // The 29,5%/49,1% pair is the strongest claim on the page and it is not
    // ours. An uncredited figure is indistinguishable from an invented one.
    expect(screen.getByText(/Int J Qual Health Care 2007;19\(2\)/)).toBeInTheDocument();
  });

  it("does not price-compete on numbers that are not true", () => {
    render(<LandingPage />);

    // Certified medical translation in Vietnam is 60-160k VND per page, not
    // USD 25-100. The argument is time and coverage, not price.
    expect(screen.queryByText(/25–100 USD/)).not.toBeInTheDocument();
    expect(screen.getByText(/không thay thế phiên dịch viên/)).toBeInTheDocument();
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
    expect(screen.getByText(/21.2 million/)).toBeInTheDocument();
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

  it("lets a clinic say which function it wants a pilot of", () => {
    render(<LandingPage />);

    // The selector used to be hidden and pinned to "scribe", left over from the
    // two-product site. This page leads with the bilingual visit, so a pilot
    // enquiry was arriving tagged as the wrong product.
    fireEvent.click(screen.getByText("Dành cho cơ sở muốn thí điểm CarePath"));
    expect(screen.getByRole("combobox", { name: "Chức năng quan tâm" })).toBeInTheDocument();
  });

  it("offers the demo from the landing page", () => {
    render(<LandingPage />);

    // The page's central claim is that CarePath reads Vietnamese paperwork, and
    // until now a visitor had no way to check that without contacting anyone.
    expect(screen.getByRole("link", { name: "Mở bản thử" })).toHaveAttribute(
      "href",
      "/thu-nghiem/",
    );
  });

  it("names the three moments the harm evidence points at", () => {
    render(<LandingPage />);

    expect(screen.getByRole("heading", { name: "Đối chiếu thuốc" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Lúc ra viện" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Khi ký cam kết" })).toBeInTheDocument();
    // The reason an interpreter alone does not cover this.
    expect(screen.getByText(/Cả ba thời điểm trên đều xảy ra sau đó/)).toBeInTheDocument();
  });
});
