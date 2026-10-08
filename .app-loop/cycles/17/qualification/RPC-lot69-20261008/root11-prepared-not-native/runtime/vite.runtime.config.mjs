import { defineConfig, mergeConfig } from "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/node_modules/vite/dist/node/index.js";
import canonical from "/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/vite.canonique.mjs";
export default defineConfig(async () => {
  const configEnv = {command: 'serve', mode: 'development'};
  const canonicalConfig = await Promise.resolve(typeof canonical === 'function' ? canonical(configEnv) : canonical);
  if (!canonicalConfig) throw new Error('Configuration Vite canonique absente');
  return mergeConfig(canonicalConfig, {
    root: "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend", envDir: "/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/profiles/service", cacheDir: "/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3/runtime/vite-cache",
    server: {host: '127.0.0.1', port: 5173, strictPort: true,
      fs: {allow: ["/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source", "/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source/src/frontend/node_modules"]}}
  });
});
