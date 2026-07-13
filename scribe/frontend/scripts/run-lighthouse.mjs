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
