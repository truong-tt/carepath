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
// them for bandwidth and make this worse. 700 is tool-heading weight and is not
// above the fold on any route, so it stays discovered from CSS.
//
// Both subsets of each weight are preloaded on purpose. Fontsource splits by
// unicode-range and Vietnamese prose needs both: the vietnamese subset carries
// the precomposed diacritics, the latin subset carries everything ASCII.
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
        )
        .join("");
      // Ahead of the stylesheet, not before </head>. Appended last, the preload
      // was discovered no earlier than the @font-face rule it was meant to beat,
      // so it bought nothing. The stylesheet is render-blocking either way.
      const stylesheet = html.match(/<link[^>]+rel="stylesheet"[^>]*>/);
      return stylesheet
        ? html.replace(stylesheet[0], `${links}${stylesheet[0]}`)
        : html.replace("</head>", `${links}</head>`);
    },
  };
}

// Dev mirrors the Vercel rewrite so /api/* is same-origin here too, and the
// tools work against a local backend without a VITE_API_BASE or a CORS entry.
// Point CAREPATH_DEV_API at the Space to develop the UI against production.
const DEV_API = process.env.CAREPATH_DEV_API ?? "http://127.0.0.1:8000";

// The /api/demo/* quota endpoints are Vercel functions and do not exist under
// `vite dev`, which would leave the public demo the one surface nobody can run
// locally. Mount the same handler modules on the dev server so what is tested
// here is the code that ships, not an approximation of it.
function demoFunctions(): Plugin {
  return {
    name: "carepath-demo-functions",
    apply: "serve",
    configureServer(server) {
      // Point the functions at the same backend the proxy uses, so `npm run
      // dev` is coherent by default instead of quietly calling production.
      process.env.DEMO_API_BASE ??= DEV_API;
      server.middlewares.use(async (req, res, next) => {
        const path = (req.url ?? "").split("?")[0];
        const match = /^\/api\/demo\/(document|session)$/.exec(path);
        if (!match) return next();
        try {
          const module = await server.ssrLoadModule(`/api/demo/${match[1]}.ts`);
          await module.default(req, res);
        } catch (error) {
          next(error as Error);
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), preloadLandingFonts(), demoFunctions()],
  server: {
    proxy: {
      "/api": { target: DEV_API, changeOrigin: true },
      "/ws": { target: DEV_API, changeOrigin: true, ws: true },
    },
  },
  test: {
    environment: "jsdom",
    exclude: ["tests/**", "scripts/**", "node_modules/**", "dist/**"],
    setupFiles: "./src/setupTests.ts",
  },
});
