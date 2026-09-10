/**
 * Cycle 6, lecteurs #229 et #230 (stores/openclawStore.ts).
 * - #229 : annuler une session en cours laissait `runningCount` tel quel ; le
 *   compteur « agents actifs » restait faux jusqu'au prochain rechargement et
 *   pouvait bloquer « Nouvelle tâche » à tort.
 * - #230 : un échec de lecture des messages restait muet ; une panne se lisait
 *   comme une session sans message.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  cancelOpenClawSession: vi.fn(),
  getOpenClawSessionMessages: vi.fn(),
}));
vi.mock('../services/api/agents', async () => {
  const reel = await vi.importActual<typeof import('../services/api/agents')>('../services/api/agents');
  return { ...reel, ...api };
});

import { ApiError } from '../services/api/core';
import { useOpenClawStore } from './openclawStore';

const session = (id: string, status: string) =>
  ({ id, status, instruction: 'x', created_at: '2026-09-10T00:00:00Z' }) as never;

describe('#229 : annuler une session décrémente le compteur d’agents actifs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.cancelOpenClawSession.mockResolvedValue({});
  });

  it('une session en cours annulée fait passer le compteur de 2 à 1', async () => {
    useOpenClawStore.setState({ sessions: [session('s1', 'running'), session('s2', 'running')], runningCount: 2, error: null });
    await useOpenClawStore.getState().cancelSession('s1');
    expect(useOpenClawStore.getState().runningCount).toBe(1);
    expect(useOpenClawStore.getState().sessions[0].status).toBe('cancelled');
  });

  it('annuler une session déjà terminée ne touche pas au compteur', async () => {
    useOpenClawStore.setState({ sessions: [session('s3', 'done')], runningCount: 0, error: null });
    await useOpenClawStore.getState().cancelSession('s3');
    expect(useOpenClawStore.getState().runningCount).toBe(0);
  });
});

describe('#230 : une panne de lecture des messages est signalée', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useOpenClawStore.setState({ error: null, activeSessionMessages: [] });
  });

  it('un 500 pose une erreur lisible', async () => {
    api.getOpenClawSessionMessages.mockRejectedValue(new ApiError(500, 'Internal Server Error', 'Le service est indisponible'));
    await useOpenClawStore.getState().fetchSessionMessages('s1');
    expect(useOpenClawStore.getState().error).toMatch(/Messages non lus/);
  });

  it('un 404 (session sans message pour l’instant) reste silencieux', async () => {
    api.getOpenClawSessionMessages.mockRejectedValue(new ApiError(404, 'Not Found'));
    await useOpenClawStore.getState().fetchSessionMessages('s1');
    expect(useOpenClawStore.getState().error).toBeNull();
    expect(useOpenClawStore.getState().activeSessionMessages).toEqual([]);
  });
});
