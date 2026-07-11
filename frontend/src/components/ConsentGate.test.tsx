import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConsentGate } from "./ConsentGate";

describe("ConsentGate", () => {
  it("requires both consent checks before starting", () => {
    const onConsent = vi.fn();

    render(<ConsentGate error={null} isSubmitting={false} onConsent={onConsent} />);

    const start = screen.getByRole("button", { name: "Bắt đầu phiên dịch" });
    expect(start).toBeDisabled();
    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
    expect(
      screen.getByText(/CarePath chỉ hỗ trợ phiên dịch/),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByLabelText(/Tôi đã được giải thích rằng bản dịch do AI tạo ra có thể có lỗi/),
    );
    expect(start).toBeDisabled();

    fireEvent.click(
      screen.getByLabelText(/Tôi đã được giải thích rằng có thể yêu cầu thông dịch viên trực tiếp/),
    );
    expect(start).toBeEnabled();

    fireEvent.click(start);
    expect(onConsent).toHaveBeenCalledWith(
      expect.objectContaining({
        ai_disclosure: true,
        interpreter_right: true,
        scope: "translation_aid",
      }),
    );
  });

  it("announces a startup error", () => {
    render(<ConsentGate error="Không thể bắt đầu phiên dịch." isSubmitting={false} onConsent={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Không thể bắt đầu phiên dịch.");
  });

  it("keeps the English companion marked as English", () => {
    render(<ConsentGate error={null} isSubmitting={false} onConsent={vi.fn()} />);
    expect(screen.getByText(/AI-generated translations can contain errors/)).toHaveAttribute("lang", "en");
  });
});
