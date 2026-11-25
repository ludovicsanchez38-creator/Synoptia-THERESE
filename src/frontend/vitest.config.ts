import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { searchForWorkspaceRoot } from 'vite';

const guide = resolve(__dirname, '../../docs/USER_GUIDE_ALPHA.md');

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: [
        searchForWorkspaceRoot(__dirname),
        guide,
        `${guide}?raw`,
        resolve(__dirname, '../../docs/guide-0.85'),
      ],
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
});
