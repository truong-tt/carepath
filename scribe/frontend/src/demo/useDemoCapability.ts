import { useEffect, useState } from "react";

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

/**
 * What the demo can honestly offer right now.
 *
 * - `full`   — the reader is live, so an uploaded document is really read.
 * - `sample` — scripted mode only. Samples still run the normalizer, glossary,
 *              risk engine and gate for real, but `read_document` ignores the
 *              uploaded bytes, so own-upload is hidden rather than faked.
 * - `off`    — no reader at all. Show nothing rather than something invented.
 *
 * Read from the interpreter's own health route, not the scribe's: they report
 * different halves of the process and only this one names provider_mode.
 */
export type DemoCapability = "checking" | "full" | "sample" | "off";

export function useDemoCapability(): DemoCapability {
  const [capability, setCapability] = useState<DemoCapability>("checking");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/health`)
      .then((response) => {
        if (!response.ok) throw new Error(String(response.status));
        return response.json();
      })
      .then((body: { provider_mode?: string }) => {
        if (cancelled) return;
        if (body.provider_mode === "ckey") setCapability("full");
        else if (body.provider_mode === "demo") setCapability("sample");
        else setCapability("off");
      })
      .catch(() => {
        // Fail closed. An unreachable backend must not present a demo that
        // looks available and then produces nothing.
        if (!cancelled) setCapability("off");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return capability;
}
