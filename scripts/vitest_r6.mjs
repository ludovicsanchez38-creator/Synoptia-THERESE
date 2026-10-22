/** Vitest réel, configuration du dépôt, caches confinés au worktree. */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const root = resolve(import.meta.dirname, '..');
const frontend = resolve(process.argv[2]);
process.chdir(frontend);
const require = createRequire(resolve(root, 'src/frontend/package.json'));
const { parseCLI, startVitest } = await import(pathToFileURL(require.resolve('vitest/node')));
const { filter, options } = parseCLI(['vitest', ...process.argv.slice(3)]);
const ctx = await startVitest('test', filter,
  { ...options, configLoader: 'runner' },
  { cacheDir: resolve(root, '.recette-r6/cache', frontend.includes('/base/') ? 'avant' : 'apres'),
    test: { cache: false } });
if (!ctx) process.exitCode = 1;
else {
  if (ctx.state.getFiles().some(f => f.result?.state === 'fail') || ctx.state.getUnhandledErrors().length) process.exitCode = 1;
  await ctx.close();
}
