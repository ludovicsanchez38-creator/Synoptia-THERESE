// B-1044 : une lecture globale ne doit jamais publier les canaris de signature.
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, it } from 'vitest';

function prefixes() {
  const source = readFileSync(resolve(__dirname, '../../vite.config.ts'), 'utf8');
  const tableau = /envPrefix:\s*(\[[^\]]*\])/.exec(source)?.[1];
  expect(tableau).toBeDefined();
  return JSON.parse(tableau!.replaceAll("'", '"')) as string[];
}

function verifierCanaris(canari: string) {
  // Node séparé : esbuild ne fonctionne pas dans le contexte DOM simulé.
  // Environnement du fils limité à ces valeurs fictives ; aucun fichier écrit.
  const script = `
    import { build } from 'vite';
    const { envPrefix, canari } = JSON.parse(await new Promise(resolve => {
      let texte = ''; process.stdin.on('data', morceau => texte += morceau);
      process.stdin.on('end', () => resolve(texte));
    }));
    process.env.TAURI_SIGNING_PRIVATE_KEY = canari + '-cle';
    process.env.TAURI_SIGNING_PRIVATE_KEY_PASSWORD = canari + '-phrase';
    process.env.TAURI_ENV_PLATFORM = canari + '-plateforme';
    process.env.VITE_C19_PUBLIC = canari + '-public';
    const resultat = await build({ configFile: false, envDir: false, envPrefix,
      logLevel: 'silent', plugins: [{ name: 'canari',
        resolveId: id => id === 'canari' ? '\\0canari' : undefined,
        load: id => id === '\\0canari' ? 'console.log(JSON.stringify(import.meta.env))' : undefined,
      }], build: { write: false, minify: false, rollupOptions: { input: 'canari' } },
    });
    const code = resultat.output.filter(r => r.type === 'chunk').map(r => r.code).join('');
    console.log(JSON.stringify(['-cle', '-phrase', '-plateforme', '-public'].map(s => code.includes(canari + s))));
  `;
  const resultat = spawnSync(process.execPath, ['--input-type=module', '-e', script], {
    cwd: resolve(__dirname, '../..'), input: JSON.stringify({ envPrefix: prefixes(), canari }),
    encoding: 'utf8', env: { NODE_ENV: 'test' },
  });
  expect(resultat.status, resultat.stderr).toBe(0);
  return JSON.parse(resultat.stdout.trim()) as boolean[];
}

it('exclut la signature et conserve les variables publiques Vite et Tauri', () => {
  expect(verifierCanaris('CANARI-C19')).toEqual([false, false, true, true]);
  expect(prefixes()).toEqual(['VITE_', 'TAURI_ENV_']);
});

it.each(['AULNE', 'HETRE', 'NOYER', 'FRENE', 'IF', 'ORMEAU', 'CEDRAT', 'SAULE', 'PIN', 'OLIVIER'])(
  'rejeu du bundle avec le canari %s', (nom) => {
    expect(verifierCanaris(`C19-${nom}-2026`)).toEqual([false, false, true, true]);
  },
);
