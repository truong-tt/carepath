import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  it("keeps interpreter controls unmounted before consent", () => {
    vi.stubGlobal("fetch", vi.fn());

    render(<App />);

    expect(screen.getByText("Hôm nay bạn là ai?")).toBeInTheDocument();
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
    expect(document.documentElement).toHaveAttribute("lang", "en");
    expect(document.title).toBe("CarePath | Medical Interpreter");
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
  });

  it("uses a valid language query once and defaults invalid values to Vietnamese", () => {
    window.history.replaceState({}, "", "?lang=en");
    localStorage.setItem("carepath-demo-language", "vi");
    const { unmount } = render(<App />);

    expect(document.documentElement).toHaveAttribute("lang", "en");
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
    unmount();

    window.history.replaceState({}, "", "?lang=invalid");
    render(<App />);
    expect(document.documentElement).toHaveAttribute("lang", "vi");

    window.history.replaceState({}, "", "/");
  });

  it("renders review only at the internal hash route and returns to the interpreter entry", () => {
    window.history.replaceState({}, "", "/phien-dich-y-khoa/#/kiem-duyet");
    const { unmount } = render(<App />);

    expect(screen.getByRole("heading", { name: "Translation review" })).toBeInTheDocument();
    const returnLink = screen.getByRole("link", { name: "Quay lại phiên dịch" });
    expect(returnLink).toHaveAttribute("href", "#/");

    window.location.hash = "#/";
    fireEvent(window, new HashChangeEvent("hashchange"));
    expect(screen.getByText("Hôm nay bạn là ai?")).toBeInTheDocument();

    unmount();
    window.history.replaceState({}, "", "/");
  });
});
