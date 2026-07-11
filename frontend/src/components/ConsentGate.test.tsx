import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConsentGate } from "./ConsentGate";

describe("ConsentGate", () => {
  it("requires both consent checks before starting", () => {
    const onConsent = vi.fn();

    render(<ConsentGate error={null} isSubmitting={false} onConsent={onConsent} />);

    const start = screen.getByRole("button", { name: "Tiếp tục phiên dịch" });
    expect(start).toBeDisabled();
    expect(screen.getByText("Medical Interpreter")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Phiên dịch khám bệnh trực tiếp" })).toBeInTheDocument();
    expect(
      screen.getByText(/CarePath chỉ hỗ trợ phiên dịch/),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByLabelText(/Bản dịch AI có thể có lỗi/),
    );
    expect(start).toBeDisabled();

    fireEvent.click(
      screen.getByLabelText(/Có thể yêu cầu thông dịch viên bất cứ lúc nào/),
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
});
