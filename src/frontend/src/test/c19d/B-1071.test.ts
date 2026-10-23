import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1071 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/prototype/PrototypeUnifiedViewCanvas.tsx', 'utf8');
  expect(source.includes('aria-label="Retour à l’écran précédent"')).toBe(true);
});
