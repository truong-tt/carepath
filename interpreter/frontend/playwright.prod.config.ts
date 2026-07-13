import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "production-base.spec.ts",
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:8001",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "npm.cmd run build && set ASR_PROVIDER=mock&& set ALLOW_MOCK_ASR=true&& set LLM_PROVIDER=offline&& set PROVIDER_MODE=mock&& ..\\..\\.venv\\Scripts\\python.exe -m uvicorn carepath.main:app --app-dir ..\\..\\scribe --host 127.0.0.1 --port 8001",
    url: "http://127.0.0.1:8001/phien-dich-y-khoa/",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
