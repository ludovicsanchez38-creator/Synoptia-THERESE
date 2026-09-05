/**
 * B-571 (05/09/2026) : le résultat d'une action tombait dans une conversation
 * improvisée « Nouvelle conversation ». Il ouvre une conversation nommée
 * d'après l'action, non réputée synchronisée.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api/actions', () => ({ fetchActions: vi.fn(), runAction: vi.fn(), fetchTask: vi.fn(), cancelTask: vi.fn() }));

import { insertResultInChat } from './actionsStore';
import { useChatStore } from './chatStore';
import type { TaskState } from '../services/api/actions';

const terminee = (id: string): TaskState => ({
  task_id: id, agent_id: 'audit-tresorerie', agent_name: 'Audit trésorerie', status: 'completed', params: {}, steps: [],
  result: '# Audit\n\nSolde sain.', created_at: '', started_at: null, completed_at: null, error: null, progress: 1,
});

describe('actionsStore : le résultat ouvre une conversation nommée (B-571)', () => {
  beforeEach(() => {
    useChatStore.setState({ conversations: [], currentConversationId: null });
  });

  it('la conversation porte le nom de l’action et n’est pas réputée synchronisée', () => {
    insertResultInChat(terminee('T-571'));
    const { conversations, currentConversationId } = useChatStore.getState();
    const courante = conversations.find((c) => c.id === currentConversationId);
    expect(courante?.title).toBe('Audit trésorerie');
    expect(courante?.synced).toBe(false);
    expect(courante?.messages.map((m) => m.content)).toEqual([expect.stringContaining('Solde sain.')]);
  });
});
