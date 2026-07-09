import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("renders the Vietnamese evidence-led page", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("heading", {
        name: /Phiên dịch và ghi chép y khoa, xác nhận trước khi sử dụng/,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Nội dung quan trọng không tự động đi thẳng tới người bệnh hay hồ sơ.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Từ lời nói trong buổi khám thành bản nháp SOAP.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("TODO-pricing")).toBeInTheDocument();
  });

  it("renders the complete page in English", () => {
    render(<LandingPage language="en" />);

    expect(
      screen.getByRole("heading", {
        name: /Medical interpreting and notes, confirmed before use/,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Important content does not pass straight to the patient or the record.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Status-quo costs need honest context.",
      }),
    ).toBeInTheDocument();
  });

  it("reflects clinic customization in the demo and form", () => {
    render(<LandingPage language="vi" />);

    const clinic = screen.getByRole("textbox", { name: "Tên cơ sở" });
    fireEvent.change(clinic, { target: { value: "Phòng khám Minh Tâm" } });

    expect(
      screen.getByRole("heading", { name: "Phòng khám Minh Tâm — Demo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Cơ sở y tế" }),
    ).toHaveValue("Phòng khám Minh Tâm");

    fireEvent.click(
      screen.getByRole("button", {
        name: /Kiểm tra dị ứng — xác nhận phủ định/,
      }),
    );
    expect(
      (
        screen.getByRole("textbox", {
          name: "Lời nhắn",
        }) as HTMLTextAreaElement
      ).value,
    ).toContain("Kiểm tra dị ứng — xác nhận phủ định");
  });
});
