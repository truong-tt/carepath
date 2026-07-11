import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig(({ command }) => ({
  // Production builds are served by the combined API at /phien-dich-y-khoa/; dev and
  // e2e keep the root base so the Vite dev server works unchanged.
  base: command === "build" ? "/phien-dich-y-khoa/" : "/",
  plugins: [react()],
  test: {
    environment: "jsdom",
    exclude: ["tests/**", "node_modules/**", "dist/**"],
    setupFiles: "./src/setupTests.ts",
  },
}));
