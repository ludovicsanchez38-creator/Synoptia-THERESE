import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1065 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/files/FileBrowser.tsx', 'utf8');
  expect(source.includes('aria-label="Répertoire personnel (~)"')).toBe(true); expect(source.includes('aria-label="Dossier racine"')).toBe(false);
});
