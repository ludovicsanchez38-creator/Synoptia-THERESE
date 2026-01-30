import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
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
});
