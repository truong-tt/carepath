import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";
import { copyFor, type ProductKey } from "./content/strings";

function expectProductCopy(language: "vi" | "en") {
  const copy = copyFor(language);
  for (const key of ["interpreter", "scribe"] satisfies ProductKey[]) {
    const product = copy.products[key];
    expect(screen.getAllByText(product.name).length).toBeGreaterThan(0);
    expect(screen.getAllByText(product.body).length).toBeGreaterThan(0);
    expect(screen.getAllByText(product.audience).length).toBeGreaterThan(0);
    expect(screen.getAllByText(product.status).length).toBeGreaterThan(0);
    expect(screen.getByText(product.helper)).toBeInTheDocument();
    expect(screen.getByText(product.preview)).toBeInTheDocument();
    expect(screen.getByText(product.timing)).toBeInTheDocument();
    expect(screen.getByText(product.chooserSafety)).toBeInTheDocument();
    expect(screen.getByRole("link", {
      name: `${product.name}: ${product.cta.open}`,
    })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: product.cta.open })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: product.cta.pilot }),
    ).toBeInTheDocument();
  }
}

describe("LandingPage", () => {
  it("renders the Vietnamese evidence-led page", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Bạn muốn hỗ trợ việc gì hôm nay?",
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
    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ghi chép bệnh án AI" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "1. Phiên âm tự động" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "3. Bản ghi y khoa theo bốn mục SOAP" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("TODO-pricing")).not.toBeInTheDocument();
    expectProductCopy("vi");
  });

  it("renders the complete page in English", () => {
    render(<LandingPage language="en" />);

    expect(screen.getByRole("heading", {
      name: "Choose the right product for the right point in care.",
    })).toBeInTheDocument();
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
    ).toHaveLength(1);
    expect(
      screen.getAllByText("Pilot tool — every draft requires clinician review."),
    ).toHaveLength(1);
    expectProductCopy("en");
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
