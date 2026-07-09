import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConsentGate } from "./ConsentGate";

describe("ConsentGate", () => {
  it("requires both consent checks before starting", () => {
    const onConsent = vi.fn();

    render(<ConsentGate error={null} isSubmitting={false} onConsent={onConsent} />);

    const start = screen.getByRole("button", { name: "Start session" });
    expect(start).toBeDisabled();
    expect(screen.getByText("Thông báo sử dụng AI")).toBeInTheDocument();
    expect(screen.getByText("Công cụ phiên dịch")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Công cụ này chỉ phiên dịch lời nói. Kết quả có thể sai và không thay thế lời khuyên y tế, chẩn đoán, hoặc khuyến nghị dùng thuốc.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByLabelText("AI translation may contain errors. / Bản dịch AI có thể có lỗi."),
    );
    expect(start).toBeDisabled();

    fireEvent.click(
      screen.getByLabelText(
        "A human interpreter can be requested at any time. / Có thể yêu cầu thông dịch viên bất cứ lúc nào.",
      ),
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
});
