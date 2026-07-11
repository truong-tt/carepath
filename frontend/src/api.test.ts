import { afterEach, describe, expect, it, vi } from "vitest";

import { deleteSession, endSession } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("session lifecycle API", () => {
  it("calls the existing end and delete endpoints", async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetch);

    await endSession("session-1");
    await deleteSession("session-1");

    expect(fetch).toHaveBeenNthCalledWith(1, expect.stringContaining("/api/sessions/session-1/end"), { method: "POST" });
    expect(fetch).toHaveBeenNthCalledWith(2, expect.stringContaining("/api/sessions/session-1"), { method: "DELETE" });
  });
});
