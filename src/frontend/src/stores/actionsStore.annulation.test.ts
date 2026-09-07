/**
 * B-584 : après une demande d'annulation, la tâche reste en `cancel_requested`
 * et le sondage était arrêté : l'écran affichait « Arrêt en cours » sans fin.
 * Le suivi doit reprendre jusqu'à un état final.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api/actions', () => ({
  fetchAgents: vi.fn(),
  launchTask: vi.fn(),
  fetchTask: vi.fn(),
  cancelTask: vi.fn(),
}));

import { cancelTask, fetchTask } from '../services/api/actions';
import type { TaskState } from '../services/api/actions';
import { useActionsStore } from './actionsStore';

const tache = (status: TaskState['status']): TaskState => ({
  task_id: 'T1', agent_id: 'relance', agent_name: 'Relance clients', status, params: {}, steps: [],
  result: '', created_at: '', started_at: null, completed_at: null, error: null, progress: 0.5,
});

describe('B-584 - une annulation demandée est suivie jusqu’à son terme', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useActionsStore.setState({ tasks: [tache('running')], activeTask: null, error: null });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('le sondage reprend après cancel_requested et s’arrête sur cancelled', async () => {
    vi.mocked(cancelTask).mockResolvedValue(undefined as never);
    vi.mocked(fetchTask)
      .mockResolvedValueOnce(tache('cancel_requested' as TaskState['status']))
      .mockResolvedValue(tache('cancelled'));

    await useActionsStore.getState().cancelTask('T1');
    expect(useActionsStore.getState().tasks[0].status).toBe('cancel_requested');
    expect(vi.getTimerCount()).toBeGreaterThan(0);

    for (let i = 0; i < 6; i++) await vi.advanceTimersByTimeAsync(1500);

    expect(useActionsStore.getState().tasks[0].status).toBe('cancelled');
    expect(vi.getTimerCount()).toBe(0);
  });
});
