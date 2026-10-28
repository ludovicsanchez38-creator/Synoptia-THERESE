import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.', testMatch: 'c22a.spec.ts', workers: 1, retries: 0,
  reporter: [['list']], outputDir: '../../test-results/c22a',
  use: { baseURL: 'http://127.0.0.1:14383', browserName: 'chromium', viewport: { width: 1280, height: 800 } },
  webServer: {
    command: 'nice -n 10 npm --prefix src/frontend run dev -- --host 127.0.0.1 --port 14383 --strictPort',
    cwd: '../..', url: 'http://127.0.0.1:14383/tests/recette-c22a.html', reuseExistingServer: false,
    timeout: 60000,
  },
});
