/**
 * B-304 - une action dont le SUIVI échoue restait « en cours » à vie.
 *
 * `refreshTask` avalait l'erreur dans un catch vide : ni message, ni changement
 * de statut. Et `_startPolling` reprogrammait un sondage toutes les 1,5 s tant
 * que le statut n'était pas final - condition qui, l'échec ne changeant rien,
 * restait vraie pour toujours. Mesuré avant correctif : onze appels à
 * `fetchTask`, statut « running », `store.error` à null.
 *
 * Le compteur doit se remettre à zéro au premier succès : une coupure réseau
 * passagère ne doit pas tuer un suivi qui allait aboutir.
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

const tacheEnCours = (): TaskState => ({
  task_id: 'T1',
  agent_id: 'prep-rdv',
  agent_name: 'Préparation RDV',
  status: 'running',
  params: {},
  steps: [],
  result: '',
  created_at: '',
  started_at: null,
  completed_at: null,
  error: null,
  progress: 0.3,
});

function demarrerSondage() {
  (useActionsStore.getState() as unknown as { _startPolling: (id: string) => void })._startPolling(
    'T1',
  );
}

describe('B-304 - un suivi qui échoue finit par le dire', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useActionsStore.setState({ tasks: [tacheEnCours()], activeTask: null, error: null });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('après des échecs répétés, le sondage s’arrête et un message apparaît', async () => {
    vi.mocked(fetchTask).mockRejectedValue(new Error('Failed to fetch'));

    demarrerSondage();
    await vi.advanceTimersByTimeAsync(1000);
    for (let i = 0; i < 10; i++) await vi.advanceTimersByTimeAsync(1500);

    const etat = useActionsStore.getState();
    expect(vi.getTimerCount()).toBe(0);
    expect(etat.error).toBeTruthy();
    expect(etat.tasks[0].status).not.toBe('running');
  });

  it('un échec isolé suivi d’un succès ne coupe pas le suivi', async () => {
    vi.mocked(fetchTask)
      .mockRejectedValueOnce(new Error('Failed to fetch'))
      .mockResolvedValue({ ...tacheEnCours(), progress: 0.6 });

    demarrerSondage();
    await vi.advanceTimersByTimeAsync(1000);
    for (let i = 0; i < 6; i++) await vi.advanceTimersByTimeAsync(1500);

    const etat = useActionsStore.getState();
    expect(etat.error).toBeNull();
    expect(etat.tasks[0].status).toBe('running');
    expect(etat.tasks[0].progress).toBe(0.6);
    // Le suivi est toujours armé : la tâche n'est pas terminée.
    expect(vi.getTimerCount()).toBeGreaterThan(0);
  });

  it('deux échecs puis un succès : le compteur est remis à zéro', async () => {
    vi.mocked(fetchTask)
      .mockRejectedValueOnce(new Error('coupure 1'))
      .mockRejectedValueOnce(new Error('coupure 2'))
      .mockResolvedValueOnce({ ...tacheEnCours(), progress: 0.7 })
      .mockRejectedValueOnce(new Error('coupure 3'))
      .mockRejectedValueOnce(new Error('coupure 4'))
      .mockResolvedValue({ ...tacheEnCours(), progress: 0.9 });

    demarrerSondage();
    await vi.advanceTimersByTimeAsync(1000);
    for (let i = 0; i < 8; i++) await vi.advanceTimersByTimeAsync(1500);

    const etat = useActionsStore.getState();
    expect(etat.error).toBeNull();
    expect(etat.tasks[0].status).toBe('running');
  });
});
