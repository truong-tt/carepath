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

test("requires the API base", () => {
  assert.throws(() => validateDeployEnv({}), /VITE_API_BASE is required/);
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
  assert.deepEqual(config.rewrites, [
    { source: "/ghi-chep-lam-sang", destination: "/index.html" },
    { source: "/ghi-chep-lam-sang/", destination: "/index.html" },
    { source: "/ghi-chep-lam-sang/:path*", destination: "/index.html" },
    { source: "/kham-song-ngu", destination: "/index.html" },
    { source: "/kham-song-ngu/", destination: "/index.html" },
    { source: "/kham-song-ngu/:path*", destination: "/index.html" },
  ]);
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
