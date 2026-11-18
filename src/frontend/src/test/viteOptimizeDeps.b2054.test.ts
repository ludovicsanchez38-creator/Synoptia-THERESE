import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { beforeAll, expect, it } from 'vitest';

let parcours: { entrees: string[]; sources: string[] };

function estUnFichierDeTest(chemin: string): boolean {
  return /\.(test|spec)\.[jt]sx?$/.test(chemin)
    || /(^|\/)__tests__\//.test(chemin)
    || chemin.startsWith('src/test/');
}

beforeAll(() => {
  // Comme le test voisin viteSecrets : esbuild doit tourner hors de jsdom.
  // On charge l'export réel, sans démarrer de serveur ni résoudre de fournisseur.
  const script = `
    import { createRequire } from 'node:module';
    import { resolve } from 'node:path';
    import { loadConfigFromFile } from 'vite';
    const require = createRequire(import.meta.resolve('vite'));
    const { glob } = require('tinyglobby');
    const resultat = await loadConfigFromFile(
      { command: 'serve', mode: 'development' }, resolve('vite.config.ts'),
      process.cwd(), 'silent',
    );
    const config = resultat?.config;
    if (!config?.optimizeDeps?.entries) throw new Error('optimizeDeps.entries absent');
    const cwd = resolve(config.root ?? '.');
    // Même moteur et mêmes exclusions implicites que Vite pour des entries
    // explicites : node_modules et build.outDir, mais pas les tests.
    const entrees = await glob(config.optimizeDeps.entries, {
      cwd, ignore: ['**/node_modules/**', '**/' + (config.build?.outDir ?? 'dist') + '/**'],
    });
    const sources = await glob('src/**/*.{ts,tsx}', { cwd });
    console.log(JSON.stringify({ entrees: entrees.sort(), sources: sources.sort() }));
  `;
  const resultat = spawnSync(process.execPath, ['--input-type=module', '-e', script], {
    cwd: resolve(__dirname, '../..'), encoding: 'utf8',
    env: { NODE_ENV: 'test' }, timeout: 15_000,
  });
  expect(resultat.status, resultat.stderr || resultat.error?.message).toBe(0);
  parcours = JSON.parse(resultat.stdout.trim());
});

it('B-2054 : aucun fichier de test ne fait partie des entrées de l’optimiseur', () => {
  expect(parcours.sources.some(estUnFichierDeTest)).toBe(true);
  const fuites = parcours.entrees.filter(estUnFichierDeTest);
  expect(
    fuites.length,
    `B-2054 : ${fuites.length} fichier(s) de test dans optimizeDeps.entries (ex. ${fuites.slice(0, 3).join(', ')})`,
  ).toBe(0);
});

it('conserve index.html et toutes les sources applicatives, y compris les surfaces lazy', () => {
  const sourcesApplicatives = parcours.sources.filter((chemin) => !estUnFichierDeTest(chemin));
  expect(sourcesApplicatives.length).toBeGreaterThan(0);
  const entrees = new Set(parcours.entrees);
  expect(['index.html', ...sourcesApplicatives].filter((chemin) => !entrees.has(chemin))).toEqual([]);
});
