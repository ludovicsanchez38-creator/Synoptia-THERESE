import { defineConfig } from "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/node_modules/vite/dist/node/index.js";
import react from "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
import tailwindcss from "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/node_modules/@tailwindcss/vite/dist/index.mjs";
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  define: {
    // Identifie le serveur de développement : les forçages par URL et variable
    // Vite lui sont réservés, y compris face à `vite build --mode development`.
    __THERESE_DEV_BUILD__: JSON.stringify(command === 'serve'),
  },
  resolve: {
    alias: {
      '@': "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/src",
    },
  },
  // Tauri expects a fixed port
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
  // Env prefix for Tauri
  envPrefix: ['VITE_', 'TAURI_'],
  // B-264 : les neuf surfaces chargées en lazy() faisaient découvrir des
  // dépendances en cours de session ; Vite ré-optimisait et rechargeait la
  // page (~3 % des parcours de bout en bout). Le crawl couvre toutes les sources.
  optimizeDeps: {
    entries: ['index.html', 'src/**/*.{ts,tsx}'],
  },
  build: {
    // Tauri supports es2021
    target: process.env.TAURI_PLATFORM === 'windows' ? 'chrome105' : 'safari14',
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'vendor-react': ['react', 'react-dom'],
          // UI libraries
          'vendor-ui': ['framer-motion', 'lucide-react'],
          // Markdown rendering
          'vendor-markdown': ['react-markdown', 'react-syntax-highlighter'],
          // State management
          'vendor-state': ['zustand'],
          // Tauri APIs
          'vendor-tauri': [
            '@tauri-apps/api',
            '@tauri-apps/plugin-fs',
            '@tauri-apps/plugin-dialog',
            '@tauri-apps/plugin-shell',
          ],
        },
      },
    },
  },
  clearScreen: false,
}));
