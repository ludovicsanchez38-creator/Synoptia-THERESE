import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from '../services/api/core';

afterEach(() => vi.useRealTimers());

describe('R4c : le transport de test respecte le contrat asynchrone de fetch', () => {
  it('un appel non doublé échoue hors réseau et libère son délai', async () => {
    vi.useFakeTimers();
    const delaisAvant = vi.getTimerCount();
    const appel = apiFetch('http://127.0.0.1:1/api/activities');
    await expect(appel).rejects.toThrow('Réseau non doublé dans ce test');
    expect(vi.getTimerCount()).toBe(delaisAvant);
  });

  it('une remise à zéro des doublures conserve un rejet asynchrone', async () => {
    vi.mocked(fetch).mockReset();
    vi.useFakeTimers();
    const delaisAvant = vi.getTimerCount();
    await expect(apiFetch('http://127.0.0.1:1/api/voice/status'))
      .rejects.toThrow('Réseau non doublé dans ce test');
    expect(vi.getTimerCount()).toBe(delaisAvant);
  });
});
