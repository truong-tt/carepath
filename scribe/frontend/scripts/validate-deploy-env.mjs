import { pathToFileURL } from "node:url";

export function validateDeployEnv(env = process.env) {
  const errors = [];
  const parse = (name) => {
    const value = env[name]?.trim();
    if (!value) {
      errors.push(`${name} is required.`);
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

  const apiBase = parse("VITE_API_BASE");
  const consoleUrl = parse("VITE_CONSOLE_URL");
  if (apiBase && consoleUrl && apiBase.origin !== consoleUrl.origin) {
    errors.push("VITE_API_BASE and VITE_CONSOLE_URL must share one origin.");
  }
  if (apiBase && apiBase.pathname !== "/") {
    errors.push("VITE_API_BASE pathname must be /.");
  }
  if (consoleUrl && consoleUrl.pathname !== "/phien-dich-y-khoa/") {
    errors.push("VITE_CONSOLE_URL pathname must be /phien-dich-y-khoa/.");
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
