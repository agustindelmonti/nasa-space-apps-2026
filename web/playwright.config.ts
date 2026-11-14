import { defineConfig } from "@playwright/test";

// Uses the Chromium already installed in the environment (PLAYWRIGHT_BROWSERS_PATH);
// @playwright/test is pinned to the version that matches it, so no download is needed.
//
// Two servers: the real API (engine over cached NASA data) and Vite pointing at it. Ports are
// fixed and never reused, so a dev server without VITE_API_URL cannot leak into the run.
const API_URL = "http://127.0.0.1:8000";
const WEB_URL = "http://127.0.0.1:4173";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 30_000,
  reporter: "list",
  workers: 2,
  use: { baseURL: WEB_URL, trace: "off" },
  webServer: [
    {
      command: "uv run uvicorn rastrojo.adapters.api:app --host 127.0.0.1 --port 8000",
      cwd: "..",
      url: `${API_URL}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { CORS_ALLOWED_ORIGINS: `${WEB_URL},http://localhost:4173` },
    },
    {
      command: "npx vite --host 127.0.0.1 --port 4173 --strictPort",
      url: WEB_URL,
      reuseExistingServer: false,
      timeout: 60_000,
      env: { VITE_API_URL: API_URL },
    },
  ],
  projects: [
    { name: "projector-1920", use: { browserName: "chromium", viewport: { width: 1920, height: 1080 } } },
    { name: "projector-1280", use: { browserName: "chromium", viewport: { width: 1280, height: 720 } } },
    { name: "phone-390", use: { browserName: "chromium", viewport: { width: 390, height: 844 } } },
  ],
});
