/**
 * US-010 : persistance débouncée du chat.
 *
 * Avant : le middleware persist de Zustand écrivait dans localStorage à
 * CHAQUE updateMessage (chaque flush de phrase pendant le streaming) →
 * sérialisation JSON de toutes les conversations plusieurs fois par seconde.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createDebouncedStorage } from './debouncedStorage';

// Le setup global mocke localStorage avec des vi.fn() vides : on installe ici
// un vrai localStorage en mémoire avec compteur d'écritures.
function installRealLocalStorage() {
  const store = new Map<string, string>();
  let writes = 0;
  const real = {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => {
      writes++;
      store.set(k, String(v));
    },
    removeItem: (k: string) => {
      store.delete(k);
    },
    clear: () => store.clear(),
    key: (i: number) => Array.from(store.keys())[i] ?? null,
    get length() {
      return store.size;
    },
    get writes() {
      return writes;
    },
  };
  Object.defineProperty(window, 'localStorage', { value: real, configurable: true });
  return real;
}

describe('createDebouncedStorage (US-010)', () => {
  let real: ReturnType<typeof installRealLocalStorage>;

  beforeEach(() => {
    vi.useFakeTimers();
    real = installRealLocalStorage();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('n écrit pas immédiatement, mais après le délai', () => {
    const storage = createDebouncedStorage(400);
    storage.setItem('k', 'v1');
    expect(real.getItem('k')).toBeNull();
    vi.advanceTimersByTime(400);
    expect(real.getItem('k')).toBe('v1');
  });

  it('coalesce les écritures rapprochées (une seule écriture finale)', () => {
    const storage = createDebouncedStorage(400);
    for (let i = 0; i < 50; i++) {
      storage.setItem('k', `v${i}`);
      vi.advanceTimersByTime(5);
    }
    vi.advanceTimersByTime(400);
    expect(real.getItem('k')).toBe('v49');
    // 50 setItem en ~250ms -> au plus 2 écritures réelles (1 par fenêtre de 400ms)
    expect(real.writes).toBeLessThanOrEqual(2);
  });

  it('getItem flush l écriture en attente (lecture cohérente)', () => {
    const storage = createDebouncedStorage(400);
    storage.setItem('k', 'pending');
    expect(storage.getItem('k')).toBe('pending');
    expect(real.getItem('k')).toBe('pending');
  });

  it('removeItem annule l écriture en attente', () => {
    const storage = createDebouncedStorage(400);
    storage.setItem('k', 'pending');
    storage.removeItem('k');
    vi.advanceTimersByTime(400);
    expect(real.getItem('k')).toBeNull();
  });
});
