import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ScribeShowcase from "./ScribeShowcase";

describe("ScribeShowcase", () => {
  it("walks raw transcript, correction, and SOAP draft steps", () => {
    render(<ScribeShowcase language="vi" />);

    expect(screen.getByText("am lô đi pin")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Gạch chân: đoạn hệ thống nghe sai trong bản phiên âm tự động.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "2. Sau hiệu chỉnh thuật ngữ" }),
    );
    expect(screen.getByText("amlodipin")).toBeInTheDocument();
    expect(screen.getByText("160/90 mmHg")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "3. Bản ghi y khoa theo bốn mục SOAP",
      }),
    );
    expect(screen.getByText("Chờ bác sĩ duyệt")).toBeInTheDocument();
    expect(screen.getByText("Kế hoạch")).toBeInTheDocument();
    expect(
      screen.getByText("Tăng huyết áp chưa kiểm soát."),
    ).toBeInTheDocument();
  });

  it("localizes the frame while keeping the Vietnamese sample", () => {
    render(<ScribeShowcase language="en" />);

    expect(
      screen.getByText("Simulation with sample data, not a real record"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "3. SOAP draft" }));
    expect(screen.getByText("Awaiting clinician review")).toBeInTheDocument();
    expect(screen.getByText("Subjective")).toBeInTheDocument();
  });
});
