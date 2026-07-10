import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { validateDeployEnv } from "./validate-deploy-env.mjs";

const validEnv = {
  VITE_API_BASE: "https://carepath.hf.space",
  VITE_CONSOLE_URL: "https://carepath.hf.space/console/",
};

test("accepts one HTTPS Space origin", () => {
  assert.doesNotThrow(() => validateDeployEnv(validEnv));
});

test("requires both deployment URLs", () => {
  assert.throws(
    () => validateDeployEnv({}),
    /VITE_API_BASE is required[\s\S]*VITE_CONSOLE_URL is required/,
  );
});

test("rejects HTTP, split origins, and the wrong console path", () => {
  assert.throws(
    () =>
      validateDeployEnv({
        VITE_API_BASE: "http://api.example.test",
        VITE_CONSOLE_URL: "https://console.example.test/app/",
      }),
    /must use HTTPS[\s\S]*must share one origin[\s\S]*pathname must be \/console\//,
  );
});

test("rejects paths, queries, and fragments that would corrupt runtime URLs", () => {
  assert.throws(
    () =>
      validateDeployEnv({
        VITE_API_BASE: "https://carepath.hf.space/wrong?token=secret",
        VITE_CONSOLE_URL: "https://carepath.hf.space/console/#app",
      }),
    /VITE_API_BASE must not include a query or fragment[\s\S]*VITE_CONSOLE_URL must not include a query or fragment[\s\S]*VITE_API_BASE pathname must be \//,
  );
});

test("Vercel runs validation before the production build", async () => {
  const config = JSON.parse(
    await readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  );
  assert.equal(config.buildCommand, "npm run validate:deploy && npm run build");
});
