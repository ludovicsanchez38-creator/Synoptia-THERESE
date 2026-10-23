import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1067 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/memory/MemoryPanel.tsx', 'utf8');
  expect(source.includes('} bientôt')).toBe(true);
});
