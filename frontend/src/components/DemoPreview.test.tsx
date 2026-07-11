import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DemoPreview } from "./DemoPreview";

afterEach(() => vi.unstubAllGlobals());

describe("DemoPreview", () => {
  it("replays delivered, low-confidence, and blocked moments without browser APIs", () => {
    const getUserMedia = vi.fn();
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
    render(<DemoPreview language="vi" />);

    fireEvent.click(screen.getByRole("button", { name: "Xem mô phỏng" }));
    expect(screen.getByText("Bản dịch được chuyển")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Xem tình huống tiếp theo" }));
    expect(screen.getByText("Độ tin cậy thấp", { exact: true })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Xem tình huống tiếp theo" }));
    expect(screen.getByText("Đã chặn, chờ bác sĩ xác nhận", { exact: true })).toBeInTheDocument();

    expect(fetch).not.toHaveBeenCalled();
    expect(getUserMedia).not.toHaveBeenCalled();
  });
});
