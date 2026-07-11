import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./LandingPage";
import { copyFor, type ProductKey } from "./content/strings";

function expectProductCopy(language: "vi" | "en") {
  const copy = copyFor(language);
  for (const key of ["interpreter", "scribe"] satisfies ProductKey[]) {
    const product = copy.products[key];
    expect(screen.getAllByText(product.name).length).toBeGreaterThan(0);
    expect(screen.getByText(product.body)).toBeInTheDocument();
    expect(screen.getByText(product.audience)).toBeInTheDocument();
    expect(screen.getByText(product.input)).toBeInTheDocument();
    expect(screen.getByText(product.output)).toBeInTheDocument();
    expect(screen.getByText(product.status)).toBeInTheDocument();
    expect(screen.getByText(product.helper)).toBeInTheDocument();
    expect(screen.getByText(product.timing)).toBeInTheDocument();
    expect(screen.getByText(product.chooserSafety)).toBeInTheDocument();
    expect(screen.getByRole("link", {
      name: `${product.name}: ${product.cta.open}`,
    })).toBeInTheDocument();
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
    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ghi chép bệnh án AI" })).toBeInTheDocument();
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

  it("keeps the pilot form after the decision gateway", () => {
    render(<LandingPage language="vi" />);

    expect(
      screen.getByRole("textbox", { name: "Cơ sở y tế" }),
    ).toHaveValue("Phòng khám Đa khoa An Bình");
    expect(screen.getByRole("combobox", { name: "Chức năng quan tâm" })).toHaveValue("both");
  });
});
