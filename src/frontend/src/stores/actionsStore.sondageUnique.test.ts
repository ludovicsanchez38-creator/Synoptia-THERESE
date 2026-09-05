/**
 * B-492 : `_startPolling` reprogrammait un sondage sans conserver son
 * identifiant. Deux démarrages pour la même tâche (double clic, remontage)
 * faisaient tourner deux chaînes de setTimeout en parallèle, et rien ne les
 * arrêtait au démontage.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api/actions', () => ({
  fetchActions: vi.fn(),
  runAction: vi.fn(),
  fetchTask: vi.fn(),
  cancelTask: vi.fn(),
}));

import { useActionsStore } from './actionsStore';
import { fetchTask } from '../services/api/actions';
import type { TaskState } from '../services/api/actions';

const tache = (): TaskState => ({
  task_id: 'T9', agent_id: 'a', agent_name: 'A', status: 'running', params: {}, steps: [],
  result: '', created_at: '', started_at: null, completed_at: null, error: null, progress: 0.1,
});

type Interne = { _startPolling: (id: string) => void; _stopPolling: (id: string) => void };

describe('actionsStore - un seul sondage par tâche (B-492)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    vi.mocked(fetchTask).mockResolvedValue(tache());
    useActionsStore.setState({ tasks: [tache()], error: null });
  });
  afterEach(() => vi.useRealTimers());

  it('deux démarrages ne produisent qu’une chaîne de sondage', async () => {
    const s = useActionsStore.getState() as unknown as Interne;
    s._startPolling('T9');
    s._startPolling('T9');
    await vi.advanceTimersByTimeAsync(1000);
    expect(fetchTask).toHaveBeenCalledTimes(1);
  });

  it('_stopPolling annule la minuterie en attente', async () => {
    const s = useActionsStore.getState() as unknown as Interne;
    s._startPolling('T9');
    s._stopPolling('T9');
    await vi.advanceTimersByTimeAsync(5000);
    expect(fetchTask).not.toHaveBeenCalled();
  });
});
