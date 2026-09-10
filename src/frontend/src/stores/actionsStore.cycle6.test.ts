/**
 * Cycle 6, lecteurs #219 et #221 (stores/actionsStore.ts).
 * - #219 : un résultat qui arrive pendant qu'on rédige DÉJÀ sur le chat
 *   basculait la conversation courante sur celle du résultat, sans signal.
 * - #221 : si l'appel d'annulation échoue, le sondage déjà arrêté n'était pas
 *   relancé : la tâche restait « en cours » sans suivi (symptôme de B-584).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api/actions', () => ({
  fetchAgents: vi.fn(), launchTask: vi.fn(), fetchTask: vi.fn(), cancelTask: vi.fn(), fetchActions: vi.fn(), runAction: vi.fn(),
}));

import { cancelTask, fetchTask } from '../services/api/actions';
import type { TaskState } from '../services/api/actions';
import { insertResultInChat, useActionsStore } from './actionsStore';
import { useChatStore } from './chatStore';
import { useNavigationStore } from './navigationStore';
import { useStatusStore } from './statusStore';

const terminee = (id: string): TaskState => ({
  task_id: id, agent_id: 'audit', agent_name: 'Audit trésorerie', status: 'completed', params: {}, steps: [],
  result: 'Solde sain.', created_at: '', started_at: null, completed_at: null, error: null, progress: 1,
});

describe('#219 : un résultat ne déplace pas la conversation en cours de rédaction', () => {
  beforeEach(() => {
    useChatStore.setState({
      conversations: [{ id: 'c0', title: 'Mon brouillon', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: true }] as never,
      currentConversationId: 'c0',
    });
    useNavigationStore.setState({ activeView: 'chat', history: [] } as never);
    useStatusStore.setState({ notifications: [] });
  });

  it('sur le chat avec une conversation ouverte : elle reste courante et « Voir » est proposé', () => {
    insertResultInChat(terminee('T-219'));
    const chat = useChatStore.getState();
    expect(chat.currentConversationId).toBe('c0');
    const resultat = chat.conversations.find((c) => c.title === 'Audit trésorerie');
    expect(resultat?.messages.map((m) => m.content)).toEqual([expect.stringContaining('Solde sain.')]);
    const notif = useStatusStore.getState().notifications.at(-1);
    expect(notif?.action?.label).toBe('Voir');
    notif?.action?.onClick();
    expect(useChatStore.getState().currentConversationId).toBe(resultat?.id);
  });
});

describe('#221 : une annulation refusée reprend le sondage', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useActionsStore.setState({ tasks: [{
      task_id: 'T1', agent_id: 'relance', agent_name: 'Relance', status: 'running', params: {}, steps: [],
      result: '', created_at: '', started_at: null, completed_at: null, error: null, progress: 0.5,
    }], activeTask: null, error: null });
  });
  afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

  it('cancelTask en panne : l’erreur est dite et un minuteur de suivi est armé', async () => {
    vi.mocked(cancelTask).mockRejectedValue(new Error('Le serveur refuse'));
    vi.mocked(fetchTask).mockResolvedValue({ task_id: 'T1', status: 'running' } as never);
    await useActionsStore.getState().cancelTask('T1');
    expect(useActionsStore.getState().error).toBe('Le serveur refuse');
    expect(vi.getTimerCount()).toBeGreaterThan(0);
  });
});
