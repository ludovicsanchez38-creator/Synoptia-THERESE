import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const invoke = vi.hoisted(() => vi.fn());
vi.mock('@tauri-apps/api/core', () => ({ invoke }));

beforeEach(() => {
  vi.resetModules();
  invoke.mockReset();
  vi.useFakeTimers();
});
afterEach(() => vi.useRealTimers());

describe('B-1847 : reprise de la découverte du port', () => {
  it.each(['indisponible', 'invalide'])('réessaie après un premier port %s', async (etat) => {
    if (etat === 'indisponible') invoke.mockRejectedValue(new Error('Démarrage en cours'));
    else invoke.mockResolvedValue(0);
    const core = await import('./core');
    const premier = core.initApiBase();
    expect(core.initApiBase()).toBe(premier);
    await vi.dynamicImportSettled();
    await vi.runAllTimersAsync();
    await premier;
    expect(invoke).toHaveBeenCalledTimes(11);

    invoke.mockResolvedValue(29147);
    await core.initApiBase();
    expect(core.getApiBase()).toBe('http://127.0.0.1:29147');
    expect(invoke).toHaveBeenCalledTimes(12);
  });

  it('partage les essais concurrents et conserve un port résolu', async () => {
    invoke.mockResolvedValue(29148);
    const core = await import('./core');
    const premiere = core.initApiBase();
    expect(core.initApiBase()).toBe(premiere);
    await premiere;
    await core.initApiBase();
    expect(core.getApiBase()).toBe('http://127.0.0.1:29148');
    expect(invoke).toHaveBeenCalledTimes(1);
  });
});
