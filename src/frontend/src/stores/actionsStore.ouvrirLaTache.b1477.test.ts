/** B-1477 : rouvrir le résultat d'une action guidée depuis « Travaux ». */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  fetchActions: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  fetchTask: vi.fn(),
  cancelTask: vi.fn(),
}));
vi.mock('../services/api/actions', () => api);

import { useActionsStore } from './actionsStore';

const tache = {
  task_id: 'tache-1', agent_id: 'audit-tresorerie', agent_name: 'Audit trésorerie', status: 'completed',
  params: {}, steps: [], result: 'Trésorerie saine.', created_at: '2026-09-25T20:00:00Z',
  started_at: '2026-09-25T20:00:00Z', completed_at: '2026-09-25T20:03:00Z', error: null, progress: 1,
};

describe('B-1477 : ouvrirLaTache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useActionsStore.setState({ isPanelOpen: false, activeTask: null, selectedAgent: { id: 'x' } as never, tasks: [], error: null });
  });

  it('relit la tâche et ouvre le panneau sur son résultat', async () => {
    api.fetchTask.mockResolvedValue(tache);
    await useActionsStore.getState().ouvrirLaTache('tache-1');
    const etat = useActionsStore.getState();
    expect(api.fetchTask).toHaveBeenCalledWith('tache-1');
    expect(etat.isPanelOpen).toBe(true);
    expect(etat.selectedAgent).toBeNull();
    expect(etat.activeTask?.result).toBe('Trésorerie saine.');
  });

  it('une tâche illisible (moteur redémarré) est dite, le panneau s’ouvre quand même', async () => {
    api.fetchTask.mockRejectedValue(new Error('Task not found'));
    await useActionsStore.getState().ouvrirLaTache('tache-1');
    const etat = useActionsStore.getState();
    expect(etat.isPanelOpen).toBe(true);
    expect(etat.error).toMatch(/résultat/);
  });
});
