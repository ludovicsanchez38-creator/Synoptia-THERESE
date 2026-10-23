import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1087 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/atelier/SessionList.tsx', 'utf8');
  expect(source.includes('Relancer cette tâche')).toBe(true); expect(source.includes('Relancer cette tache')).toBe(false);
});
