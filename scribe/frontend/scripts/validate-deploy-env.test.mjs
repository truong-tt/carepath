import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { validateDeployEnv } from "./validate-deploy-env.mjs";

const validEnv = {
  VITE_API_BASE: "https://carepath.hf.space",
};

test("accepts one HTTPS Space origin", () => {
  assert.doesNotThrow(() => validateDeployEnv(validEnv));
});

test("accepts an empty API base when the websocket names its own host", () => {
  // The production shape after DEC-0021: /api/* is rewritten same-origin by
  // Vercel, so no CORS allow-list can take the site down again.
  assert.doesNotThrow(() =>
    validateDeployEnv({ VITE_API_BASE: "", VITE_WS_BASE: "https://carepath.hf.space" }),
  );
});

test("rejects an empty API base with no websocket host to fall back on", () => {
  // Both empty means the socket would target the Vercel origin, which cannot
  // proxy the upgrade — the visit screen would connect to nothing.
  assert.throws(() => validateDeployEnv({}), /VITE_WS_BASE is required/);
});

test("rejects a websocket base with a path", () => {
  assert.throws(
    () => validateDeployEnv({ VITE_WS_BASE: "https://carepath.hf.space/ws" }),
    /VITE_WS_BASE pathname must be \//,
  );
});

test("rejects HTTP", () => {
  assert.throws(
    () => validateDeployEnv({ VITE_API_BASE: "http://api.example.test" }),
    /must use HTTPS/,
  );
});

test("rejects paths, queries, and fragments that would corrupt runtime URLs", () => {
  assert.throws(
    () => validateDeployEnv({ VITE_API_BASE: "https://carepath.hf.space/wrong?token=secret" }),
    /must not include a query or fragment[\s\S]*pathname must be \//,
  );
});

test("Vercel runs validation before the production build", async () => {
  const config = JSON.parse(
    await readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  );
  assert.equal(config.buildCommand, "npm run validate:deploy && npm run build");
  const spa = config.rewrites.filter((rule) => rule.destination === "/index.html");
  assert.deepEqual(spa, [
    { source: "/thu-nghiem", destination: "/index.html" },
    { source: "/thu-nghiem/", destination: "/index.html" },
    { source: "/thu-nghiem/:path*", destination: "/index.html" },
    { source: "/ghi-chep-lam-sang", destination: "/index.html" },
    { source: "/ghi-chep-lam-sang/", destination: "/index.html" },
    { source: "/ghi-chep-lam-sang/:path*", destination: "/index.html" },
    { source: "/kham-song-ngu", destination: "/index.html" },
    { source: "/kham-song-ngu/", destination: "/index.html" },
    { source: "/kham-song-ngu/:path*", destination: "/index.html" },
  ]);
});

test("the API proxy does not swallow the demo functions", async () => {
  // /api/demo/* are serverless functions in this project. If the catch-all
  // proxied them to the Space they would 404 there, and the quota that keeps
  // anonymous traffic off the paid provider would never run.
  const config = JSON.parse(
    await readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  );
  const api = config.rewrites.find((rule) => rule.source.startsWith("/api/"));
  const pattern = new RegExp(`^${api.source}$`);
  assert.ok(pattern.test("/api/v1/health"), "product API must still be proxied");
  assert.ok(pattern.test("/api/sessions"), "product API must still be proxied");
  assert.equal(pattern.test("/api/demo/document"), false);
  assert.equal(pattern.test("/api/demo/session"), false);
});

test("the API is proxied same-origin so no CORS allow-list can break it", async () => {
  // Regression guard for the outage this fixed: moving the site to
  // carepath-medicaltranslation.vercel.app while the Space still allowed only
  // carepath-omega.vercel.app returned 400 Disallowed CORS origin on every
  // call, and both tool routes rendered "Mất kết nối máy chủ".
  const config = JSON.parse(
    await readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  );
  const api = config.rewrites.find((rule) => rule.source.startsWith("/api/"));
  assert.ok(api, "vercel.json must rewrite /api/* to the API host");
  assert.match(api.destination, /^https:\/\/[^/]+\/api\//);
  // It has to win before any SPA catch-all could swallow it.
  assert.equal(config.rewrites.indexOf(api), 0);
});

test("every SPA route the app serves has a Vercel rewrite", async () => {
  // A missing rewrite is a hard 404 on a direct visit, and /kham-song-ngu/ is
  // the demo URL. Keep this derived from the app's own route table.
  const app = await readFile(new URL("../src/App.tsx", import.meta.url), "utf8");
  const routes = [...app.matchAll(/^const \w*_?PATH = "(\/[^"]+)";$/gm)].map((m) => m[1]);
  assert.ok(routes.length >= 2, `expected app routes, found ${routes.join(", ")}`);

  const config = JSON.parse(
    await readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  );
  const sources = new Set(config.rewrites.map((rule) => rule.source));
  for (const route of routes) {
    assert.ok(sources.has(route), `vercel.json has no rewrite for ${route}`);
  }
});
