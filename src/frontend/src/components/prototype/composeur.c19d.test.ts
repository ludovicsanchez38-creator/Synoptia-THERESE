import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
it('B-1073 : la mention limite la promesse aux actions confirmées dans la conversation', () => {
  const source = readFileSync('src/components/prototype/ConversationCanvasPrototype.tsx', 'utf8');
  expect(source).not.toContain('confirmation avant tout envoi ou modification externe');
  expect(source).toContain('Dans la conversation, les cartes de confirmation précisent les actions à autoriser.');
});
