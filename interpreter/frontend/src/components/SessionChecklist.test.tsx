import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SessionChecklist } from "./SessionChecklist";

afterEach(() => localStorage.clear());

describe("SessionChecklist", () => {
  it("reflects console state and persists dismissal", () => {
    render(<SessionChecklist delivered confirmed={false} escalationLocated={false} />);
    expect(screen.getByText("✓ Đã chuyển lượt đầu tiên")).toBeInTheDocument();
    expect(screen.getByText("○ Đã hoàn tất xác nhận")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Ẩn danh sách" }));
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
    render(<SessionChecklist delivered={false} confirmed={false} escalationLocated={false} />);
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });
});
