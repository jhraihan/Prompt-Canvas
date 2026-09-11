import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8100;
const APP_PORT = 5273;

const TEST_ENV = {
  DJANGO_SETTINGS_MODULE: "config.settings.dev",
  DJANGO_SECRET_KEY: "e2e-only-key-not-used-for-anything-real-0123456789",
  DATABASE_URL: "sqlite:///e2e.sqlite3",
  CORS_ALLOWED_ORIGINS: `http://localhost:${APP_PORT}`,
  IMAGE_PROVIDER: "stub",
  MEDIA_BASE_URL: `http://localhost:${API_PORT}`,
  LOG_JSON: "False",

  GENERATION_RATE: "1000/hour",
  LOGIN_RATE: "1000/hour",
  REGISTER_RATE: "1000/hour",
  TOKEN_RATE: "1000/hour",
};

const backendDir = fileURLToPath(new URL("../backend", import.meta.url));
const venvPython = join(
  backendDir,
  ".venv",
  process.platform === "win32" ? "Scripts" : "bin",
  "python",
);

export default defineConfig({
  testDir: "./e2e",

  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],

  use: {
    baseURL: `http://localhost:${APP_PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  webServer: [
    {

      command: `${venvPython} manage.py e2e_serve ${API_PORT}`,
      cwd: backendDir,
      url: `http://localhost:${API_PORT}/api/health/`,
      env: TEST_ENV,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `npm run dev -- --port ${APP_PORT} --strictPort`,
      url: `http://localhost:${APP_PORT}`,
      env: { VITE_API_BASE_URL: `http://localhost:${API_PORT}` },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
