import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DemoPlayer from "./DemoPlayer";

afterEach(() => {
  vi.useRealTimers();
});

describe("DemoPlayer", () => {
  it("advances playback on the scripted timer", () => {
    vi.useFakeTimers();
    render(<DemoPlayer />);

    fireEvent.click(screen.getByRole("button", { name: "Bắt đầu" }));
    act(() => vi.advanceTimersByTime(4000));

    expect(screen.getByText("Chào anh, mời ngồi.")).toBeInTheDocument();
  });

  it("blocks the dosage turn until confirmation", () => {
    render(<DemoPlayer />);

    const next = screen.getByRole("button", { name: "Lượt tiếp theo" });
    for (let index = 0; index < 6; index += 1) {
      fireEvent.click(next);
    }

    expect(
      screen.getByRole("heading", { name: "Xác nhận thông tin quan trọng" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tải bản ghi demo" })).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Xác nhận và tiếp tục" }),
    );
    fireEvent.click(next);
    fireEvent.click(next);

    expect(
      screen.getByRole("button", { name: "Tải bản ghi demo" }),
    ).toBeInTheDocument();
  });

  it("stops the red-flag scenario for escalation", () => {
    render(<DemoPlayer />);

    fireEvent.click(
      screen.getByRole("button", { name: /Đau ngực — chuyển phiên dịch viên/ }),
    );
    const next = screen.getByRole("button", { name: "Lượt tiếp theo" });
    for (let index = 0; index < 5; index += 1) {
      fireEvent.click(next);
    }

    expect(
      screen.getByRole("heading", {
        name: "Ưu tiên phiên dịch viên cho nội dung nguy cơ cao",
      }),
    ).toBeInTheDocument();
  });
});
