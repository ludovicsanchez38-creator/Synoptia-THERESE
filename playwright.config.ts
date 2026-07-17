import { defineConfig, devices } from '@playwright/test';
import { E2E_BACKEND_PORT } from './tests/e2e/stories/helpers/backend';

/**
 * Revue 0.40 : les E2E ne touchent JAMAIS l'instance THÉRÈSE réelle (17293).
 * Deux serveurs dédiés sont lancés pour la suite :
 * - un backend jetable (port E2E + THERESE_DATA_DIR temporaire, détruit à la
 *   fin) via tests/e2e/run-e2e-backend.sh ;
 * - un Vite dont le frontend vise ce backend (VITE_THERESE_BACKEND_PORT).
 * reuseExistingServer est volontairement à false : réutiliser un `make dev`
 * déjà lancé ramènerait silencieusement les tests sur le port réel.
 */
export default defineConfig({
  testDir: './tests/e2e/stories',
  globalTeardown: './tests/e2e/global-teardown.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: '/tmp/qa-results.json' }],
    ['list'],
  ],
  timeout: 30000,
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
    },
  },
  use: {
    baseURL: 'http://localhost:1420',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: 'mobile',
      use: {
        ...devices['iPhone 13'],
        viewport: { width: 375, height: 667 },
      },
    },
  ],
  webServer: [
    {
      command: 'bash tests/e2e/run-e2e-backend.sh',
      url: `http://127.0.0.1:${E2E_BACKEND_PORT}/health`,
      reuseExistingServer: false,
      timeout: 120000,
      env: { THERESE_E2E_PORT: String(E2E_BACKEND_PORT) },
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:1420',
      reuseExistingServer: false,
      timeout: 60000,
      env: { VITE_THERESE_BACKEND_PORT: String(E2E_BACKEND_PORT) },
    },
  ],
});
