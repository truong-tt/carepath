import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConsentGate } from "./ConsentGate";

describe("ConsentGate", () => {
  it("requires both consent checks before starting", () => {
    const onConsent = vi.fn();

    render(<ConsentGate error={null} isSubmitting={false} onConsent={onConsent} />);

    const start = screen.getByRole("button", { name: "Start session" });
    expect(start).toBeDisabled();

    fireEvent.click(screen.getByLabelText("AI translation may contain errors."));
    expect(start).toBeDisabled();

    fireEvent.click(screen.getByLabelText("A human interpreter can be requested at any time."));
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
