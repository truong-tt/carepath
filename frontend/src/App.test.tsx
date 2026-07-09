import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  it("keeps interpreter controls unmounted before consent", () => {
    vi.stubGlobal("fetch", vi.fn());

    render(<App />);

    expect(screen.getByRole("heading", { name: "CarePath Interpreter" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Hold to talk/ })).not.toBeInTheDocument();
  });
});
