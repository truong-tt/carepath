import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  it("keeps interpreter controls unmounted before consent", () => {
    vi.stubGlobal("fetch", vi.fn());

    render(<App />);

    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Hold to talk/ })).not.toBeInTheDocument();
  });

  it("identifies Interpreter as a mock product and shares the language preference", () => {
    localStorage.clear();
    render(<App />);

    expect(screen.getByRole("navigation", { name: "Đường dẫn sản phẩm" })).toHaveTextContent(
      "CarePath/Phiên dịch khám bệnh trực tiếp",
    );
    expect(screen.getByText("Bản mô phỏng tương tác")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tất cả chức năng" })).toHaveAttribute("href", "/");

    fireEvent.click(screen.getByRole("button", { name: "EN" }));
    expect(screen.getByText("Interactive mock simulation")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "All products" })).toBeInTheDocument();
    expect(document.querySelector(".product-shell")).toHaveAttribute("lang", "en");
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
  });
});
