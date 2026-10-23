import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1074 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/settings/ProfileTab.tsx', 'utf8');
  expect(/<button[^>]*aria-label="Fermer l’aperçu THERESE.md"[^>]*>/s.test(source)).toBe(true);
});
