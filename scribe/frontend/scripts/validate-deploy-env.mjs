import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Every route the app answers must resolve to index.html on BOTH hosts.
 *
 * There is no SPA fallback in vercel.json — each route is listed explicitly.
 * `vite preview` DOES fall back, so the whole Playwright suite passes against a
 * route that 404s in production. /dich-giay-to/ shipped exactly that way: the
 * pathname check was added to App.tsx, 32 e2e tests went green, and the live
 * URL returned 404: NOT_FOUND.
 *
 * The same app is also served by FastAPI from the Hugging Face Space, where the
 * static mount 404s an unregistered deep link for the same reason. Checking
 * only vercel.json is why /dich-giay-to/ then worked on Vercel and 404'd on the
 * Space for its whole life. Both hosts are checked here now.
 *
 * This runs inside the Vercel build (`npm run validate:deploy && npm run
 * build`), so a route missing from either host fails the deploy.
 */
/**
 * The API host's route table, read from outside this package.
 *
 * Vercel's Root Directory is `scribe/frontend` but it clones the whole repo, so
 * this resolves. If it ever does not, the build must still fail — a parity
 * check that cannot see one of the two hosts is not checking parity — but it
 * should fail saying so rather than throwing a bare ENOENT into a deploy log.
 */
function readApiSource() {
  const path = join(here, "..", "..", "carepath", "main.py");
  try {
    return readFileSync(path, "utf8");
  } catch {
    throw new Error(
      `Cannot read ${path}, so SPA routes cannot be checked against the API host. ` +
        "This check needs the whole repository, not just scribe/frontend.",
    );
  }
}

export function validateRouteRewrites({
  appSource = readFileSync(join(here, "..", "src", "App.tsx"), "utf8"),
  vercelConfig = JSON.parse(readFileSync(join(here, "..", "vercel.json"), "utf8")),
  apiSource = readApiSource(),
} = {}) {
  const errors = [];
  // `const SOMETHING_PATH = "/slug/";` — the pattern App.tsx uses for routes.
  const routes = [...appSource.matchAll(/_PATH\s*=\s*"(\/[^"]*)"/g)].map((match) => match[1]);
  if (routes.length === 0) {
    errors.push("No routes found in App.tsx; the route-parity check is not looking at anything.");
  }

  const sources = new Set((vercelConfig.rewrites ?? []).map((rule) => rule.source));
  // `@app.get("/slug", include_in_schema=False)` — the pattern main.py uses.
  const served = new Set(
    [...apiSource.matchAll(/@app\.get\(\s*"(\/[^"]*)"/g)].map((match) => match[1]),
  );

  for (const route of routes) {
    const bare = route.replace(/\/$/, "");
    for (const required of [bare, `${bare}/`, `${bare}/:path*`]) {
      if (!sources.has(required)) {
        errors.push(`vercel.json has no rewrite for "${required}" (route ${route}).`);
      }
    }
    // The API host needs the bare and slash forms; it has no `:path*` concept.
    // "/" is the static mount's own root and is never registered explicitly.
    if (bare === "") continue;
    for (const required of [bare, `${bare}/`]) {
      if (!served.has(required)) {
        errors.push(`scribe/carepath/main.py serves no "${required}" (route ${route}).`);
      }
    }
  }

  if (errors.length) {
    throw new Error(`Routes are not deployable:\n- ${errors.join("\n- ")}`);
  }
  return routes;
}

export function validateDeployEnv(env = process.env) {
  const errors = [];
  const parse = (name, { allowEmpty = false } = {}) => {
    const value = env[name]?.trim();
    if (!value) {
      if (!allowEmpty) errors.push(`${name} is required.`);
      return undefined;
    }
    try {
      const url = new URL(value);
      if (url.protocol !== "https:") {
        errors.push(`${name} must use HTTPS.`);
      }
      if (url.search || url.hash) {
        errors.push(`${name} must not include a query or fragment.`);
      }
      return url;
    } catch {
      errors.push(`${name} must be a valid URL.`);
      return undefined;
    }
  };

  // VITE_CONSOLE_URL was dropped with the interpreter console: it pointed at
  // /phien-dich-y-khoa/, which is now a deliberate 404.
  //
  // Empty is now valid and is the preferred production value: vercel.json
  // rewrites /api/* to the API host, so the browser calls its own origin and no
  // CORS allow-list participates. Requiring an absolute origin here is what let
  // the domain move to carepath-medicaltranslation.vercel.app while the Space
  // still allowed only carepath-omega.vercel.app, taking both tools down with
  // 400 Disallowed CORS origin. An absolute value stays valid for the combined
  // HF Space build and for local dev against a remote API.
  const apiBase = parse("VITE_API_BASE", { allowEmpty: true });
  if (apiBase && apiBase.pathname !== "/") {
    errors.push("VITE_API_BASE pathname must be /.");
  }

  // A websocket upgrade does not survive a Vercel rewrite to an external host,
  // so /ws/* goes direct and needs an absolute origin whenever the HTTP side is
  // same-origin. Empty is only valid when VITE_API_BASE names a host to inherit.
  const wsBase = parse("VITE_WS_BASE", { allowEmpty: true });
  if (wsBase && wsBase.pathname !== "/") {
    errors.push("VITE_WS_BASE pathname must be /.");
  }
  if (!wsBase && !apiBase) {
    errors.push(
      "VITE_WS_BASE is required when VITE_API_BASE is empty: the websocket cannot be proxied same-origin.",
    );
  }
  if (errors.length) {
    throw new Error(`Invalid Vercel deployment environment:\n- ${errors.join("\n- ")}`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    validateDeployEnv();
    const routes = validateRouteRewrites();
    console.log(`Vercel deployment environment is valid. ${routes.length} routes are rewritten.`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
