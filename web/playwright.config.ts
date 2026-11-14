import { defineConfig } from "@playwright/test";

// Uses the Chromium already installed in the environment (PLAYWRIGHT_BROWSERS_PATH);
// @playwright/test is pinned to the version that matches it, so no download is needed.
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 30_000,
  reporter: "list",
  use: { baseURL: "http://localhost:4173", trace: "off" },
  webServer: {
    command: "npm run preview",
    url: "http://localhost:4173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
  projects: [
    { name: "projector-1920", use: { browserName: "chromium", viewport: { width: 1920, height: 1080 } } },
    { name: "projector-1280", use: { browserName: "chromium", viewport: { width: 1280, height: 720 } } },
    { name: "phone-390", use: { browserName: "chromium", viewport: { width: 390, height: 844 } } },
  ],
});
