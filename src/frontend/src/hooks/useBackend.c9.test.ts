/**
 * B-792 (cycle 9), NON REPRODUIT : la lecture craignait que la relance différée
 * programmée par `connect` soit annulée par le nettoyage de l'effet d'auto-démarrage
 * au passage à « error ». Le rendu déclenché par le store (useSyncExternalStore)
 * est flushé dans une microtâche AVANT la reprise de `connect`, donc le minuteur
 * est armé après le nettoyage et survit. Ce test garde ce comportement : sans lui,
 * une réorganisation des effets pourrait éteindre la reconnexion pour de bon.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ checkHealth: vi.fn() }));
vi.mock('../services/api', () => api);

import { useBackend, useBackendStore } from './useBackend';

describe('useBackend - B-792, la reconnexion persiste après un échec', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useBackendStore.getState().reset();
    api.checkHealth.mockReset();
  });
  afterEach(() => vi.useRealTimers());

  it('retente toutes les retryDelay ms jusqu’à reconnexion', async () => {
    api.checkHealth
      .mockRejectedValueOnce(new Error('ECONNREFUSED'))
      .mockRejectedValueOnce(new Error('ECONNREFUSED'))
      .mockResolvedValue({ status: 'healthy', version: '0.73.0', services: {} });

    const { result } = renderHook(() => useBackend({ retryDelay: 1000, checkInterval: 60000 }));
    await act(async () => { await Promise.resolve(); });
    expect(api.checkHealth).toHaveBeenCalledTimes(1);
    expect(result.current.status).toBe('error');

    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(api.checkHealth).toHaveBeenCalledTimes(2);
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(api.checkHealth).toHaveBeenCalledTimes(3);
    expect(result.current.status).toBe('connected');
  });
});
