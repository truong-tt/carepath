import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import App from "./App";

describe("language preference", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = "vi";
  });

  it("defaults to Vietnamese and persists a complete English switch", () => {
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(document.documentElement.lang).toBe("en");
    expect(localStorage.getItem("carepath-demo-language")).toBe("en");
    expect(
      screen.getByRole("heading", {
        name: /Clinical translation, confirmed before delivery/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "A misunderstood sentence can travel beyond one conversation.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Important translations do not automatically pass straight to the patient.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Speak. Review. Deliver only after confirmation.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Status-quo costs need honest context.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Keep the demo you just created",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Translation with confirmation built in."),
    ).toBeInTheDocument();
  });

  it("ignores an invalid stored preference", () => {
    localStorage.setItem("carepath-demo-language", "fr");
    render(<App />);

    expect(document.documentElement.lang).toBe("vi");
    expect(
      screen.getByRole("button", { name: "VI" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
