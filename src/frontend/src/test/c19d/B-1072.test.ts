import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1072 : contrat du libellé ou de la structure', () => {
  const source = readFileSync('src/components/prototype/PrototypeConversationDrawer.tsx', 'utf8');
  expect(source.includes('left-14')).toBe(true); expect(source.includes('left-16')).toBe(false);
});
