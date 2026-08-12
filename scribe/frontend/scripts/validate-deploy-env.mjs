import { pathToFileURL } from "node:url";

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
    console.log("Vercel deployment environment is valid.");
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
