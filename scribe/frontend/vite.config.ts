import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

// Fonts imported from CSS are only discovered after the stylesheet parses, so
// the page paints in the platform fallback and reflows when each subset lands.
// That is invisible on Windows, where the fallback is metrically close, and
// costs 0.27 of layout shift on Linux, where it is DejaVu Sans -- two shifts,
// one per subset. Preloading starts them with the HTML instead.
//
// Only the faces the first viewport actually uses: 800 is the headline, 400 and
// 500 are the body and the document rows. Preloading more would compete with
// them for bandwidth and make this worse.
const PRELOAD = /be-vietnam-pro-(vietnamese|latin)-(400|500|800)-normal-[^.]+\.woff2$/;

function preloadLandingFonts(): Plugin {
  return {
    name: "carepath-preload-landing-fonts",
    apply: "build",
    transformIndexHtml(html, context) {
      const links = Object.keys(context.bundle ?? {})
        .filter((name) => PRELOAD.test(name))
        .map(
          (name) =>
            `<link rel="preload" as="font" type="font/woff2" crossorigin href="/${name}">`,
        );
      return html.replace("</head>", `${links.join("")}</head>`);
    },
  };
}

export default defineConfig({
  plugins: [react(), preloadLandingFonts()],
  test: {
    environment: "jsdom",
    exclude: ["tests/**", "scripts/**", "node_modules/**", "dist/**"],
    setupFiles: "./src/setupTests.ts",
  },
});
