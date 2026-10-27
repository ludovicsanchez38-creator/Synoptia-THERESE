/**
 * Audit bêta du 27/10/2026 (A2-22) : une clé collée avec des blancs autour.
 * La règle est commune ; chaque écran qui enregistre une clé doit s'en servir.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { nettoyerCle } from './cleApi';

describe('nettoyerCle', () => {
  it.each([
    [' sk-ant-a', 'sk-ant-a'], ['sk-ant-a\n', 'sk-ant-a'], ['\tgsk_b\r\n', 'gsk_b'],
    [' BSA-c ', 'BSA-c'], ['   ', ''], ['', ''],
  ])('%j -> %j', (saisie, attendu) => {
    expect(nettoyerCle(saisie)).toBe(attendu);
  });

  it('ne touche pas l’intérieur de la clé', () => {
    expect(nettoyerCle(' sk-ant- abc ')).toBe('sk-ant- abc');
  });
});

describe('Chaque enregistrement de clé passe par la règle commune', () => {
  const lire = (chemin: string) => readFileSync(resolve(__dirname, chemin), 'utf-8');

  it.each([
    ['../components/settings/SettingsModal.tsx', 4],
    ['../components/onboarding/LLMStep.tsx', 1],
  ])('%s', (chemin, attendus) => {
    const source = lire(chemin);
    const appels = [...source.matchAll(/api\.setApiKey\([^,]+,\s*([A-Za-z]+)\)/g)].map((m) => m[1]);
    expect(appels).toHaveLength(attendus);
    for (const variable of appels) {
      expect(source).toMatch(new RegExp(`const ${variable} = nettoyerCle\\(`));
    }
  });
});
