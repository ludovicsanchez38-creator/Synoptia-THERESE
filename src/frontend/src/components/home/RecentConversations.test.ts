import { describe, it, expect } from 'vitest';
import { selectRecentConversations } from './RecentConversations';

const conv = (id: string, updatedAt: string, msgs = 1, ephemeral = false) => ({
  id, title: `Conv ${id}`,
  messages: Array(msgs).fill({ id: 'm', role: 'user', content: 'x', timestamp: new Date() }),
  createdAt: new Date(updatedAt), updatedAt: new Date(updatedAt), ephemeral,
});

describe('selectRecentConversations', () => {
  it('trie par updatedAt desc, exclut vides et éphémères, max 5', () => {
    const list = [
      conv('a', '2026-06-01'), conv('b', '2026-06-09'), conv('c', '2026-06-05'),
      conv('empty', '2026-06-08', 0), conv('eph', '2026-06-10', 1, true),
    ] as never[];
    const out = selectRecentConversations(list, 5);
    expect(out.map((c) => c.id)).toEqual(['b', 'c', 'a']);
  });
});
