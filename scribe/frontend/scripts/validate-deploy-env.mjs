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

  // VITE_CONSOLE_URL was dropped with the interpreter console: it pointed at
  // /phien-dich-y-khoa/, which is now a deliberate 404.
  const apiBase = parse("VITE_API_BASE");
  if (apiBase && apiBase.pathname !== "/") {
    errors.push("VITE_API_BASE pathname must be /.");
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
