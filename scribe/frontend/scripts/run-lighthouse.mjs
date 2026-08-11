import { chromium } from "@playwright/test";
import { launch } from "chrome-launcher";
import lighthouse from "lighthouse";
import desktopConfig from "lighthouse/core/config/desktop-config.js";
import { preview } from "vite";

const server = await preview({
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
  },
});

let chrome;
try {
  chrome = await launch({
    chromePath: chromium.executablePath(),
    chromeFlags: ["--headless", "--no-sandbox", "--disable-gpu"],
  });
  const result = await lighthouse("http://127.0.0.1:4173", {
    port: chrome.port,
    logLevel: "error",
    output: "json",
    onlyCategories: ["performance", "accessibility", "best-practices"],
  }, desktopConfig);
  if (!result) throw new Error("Lighthouse returned no report.");

  const scores = Object.fromEntries(
    Object.entries(result.lhr.categories).map(([key, category]) => [
      key,
      Math.round((category.score ?? 0) * 100),
    ]),
  );
  console.log(JSON.stringify(scores));
  console.log(
    JSON.stringify(
      Object.fromEntries(
        [
          "first-contentful-paint",
          "largest-contentful-paint",
          "speed-index",
          "total-blocking-time",
          "cumulative-layout-shift",
        ].map((key) => [key, result.lhr.audits[key]?.displayValue]),
      ),
    ),
  );

  // Name what moved. A score and a CLS number say the page shifted but not
  // what shifted, and this gate fails on CI far more readily than it does on a
  // developer machine -- the platform fallback font differs, so the same swap
  // costs 0.01 on Windows and 0.30 on the Linux runner. Without this, the only
  // way to find the element is to guess and push again.
  const shifts = result.lhr.audits["layout-shifts"]?.details?.items ?? [];
  for (const shift of shifts) {
    const score = typeof shift.score === "number" ? shift.score.toFixed(4) : "?";
    console.log(`layout shift ${score}  ${shift.node?.selector ?? "(unattributed)"}`);
  }

  for (const key of ["performance", "accessibility", "best-practices"]) {
    if ((scores[key] ?? 0) < 95) {
      throw new Error(`Lighthouse ${key} score ${scores[key]} is below 95.`);
    }
  }
} finally {
  if (chrome) {
    try {
      await chrome.kill();
    } catch (error) {
      if (!(error instanceof Error) || !error.message.includes("EPERM")) {
        console.error(error);
        process.exitCode = 1;
      }
    }
  }
  await new Promise((resolve, reject) => {
    server.httpServer.close((error) => (error ? reject(error) : resolve()));
  });
}
