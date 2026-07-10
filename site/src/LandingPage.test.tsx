import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";

describe("LandingPage", () => {
  it("renders the Vietnamese evidence-led page", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("heading", {
        name: "Một hành trình chăm sóc. Hai sản phẩm CarePath.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Một lớp giám sát chung. Hai cơ chế an toàn riêng.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Từ lời đã nói đến bản nháp có cấu trúc.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CarePath Interpreter" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CarePath Scribe" })).toBeInTheDocument();
    expect(screen.queryByText("TODO-pricing")).not.toBeInTheDocument();
  });

  it("renders the complete page in English", () => {
    render(<LandingPage language="en" />);

    expect(
      screen.getByRole("heading", {
        name: "One care journey. Two CarePath products.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "One shared oversight layer. Two product-specific safety systems.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Choose the product that fits your workflow.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Interactive simulation — not live interpreting."),
    ).toHaveLength(2);
    expect(
      screen.getAllByText("Pilot tool — every draft requires clinician review."),
    ).toHaveLength(2);
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
