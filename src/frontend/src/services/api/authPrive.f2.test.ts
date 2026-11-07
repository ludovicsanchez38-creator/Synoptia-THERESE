import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { apiFetch, getSessionToken, initializeAuth, _reinitialiserAuthPourTests } from './core';

const ipc = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock('@tauri-apps/api/core', () => ipc);

describe('F-2 : le jeton desktop passe par le fichier privé et IPC', () => {
  beforeEach(() => {
    _reinitialiserAuthPourTests();
    ipc.invoke.mockReset();
  });

  afterEach(() => {
    delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
    delete (window as unknown as Record<string, unknown>).__TAURI__;
    vi.unstubAllGlobals();
  });

  it.each(['__TAURI_INTERNALS__', '__TAURI__'])('amorce et renouvelle par IPC (%s)', async (marqueur) => {
    (window as unknown as Record<string, unknown>)[marqueur] = {};
    ipc.invoke.mockResolvedValueOnce('jeton-initial').mockResolvedValueOnce('jeton-renouvele');
    const fetchSimule = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ code: 'UNAUTHORIZED' }), { status: 401 }))
      .mockResolvedValueOnce(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchSimule);

    await initializeAuth();
    expect(getSessionToken()).toBe('jeton-initial');
    expect(fetchSimule).not.toHaveBeenCalled();

    const reponse = await apiFetch('http://127.0.0.1:17293/api/dashboard/today');

    expect(reponse.status).toBe(200);
    expect(ipc.invoke.mock.calls).toEqual([['get_session_token'], ['get_session_token']]);
    expect(fetchSimule).toHaveBeenCalledTimes(2);
    expect(fetchSimule.mock.calls.map(([url]) => url)).toEqual([
      'http://127.0.0.1:17293/api/dashboard/today',
      'http://127.0.0.1:17293/api/dashboard/today',
    ]);
    expect(fetchSimule.mock.calls.map(([, init]) => new Headers(init.headers).get('X-Therese-Token')))
      .toEqual(['jeton-initial', 'jeton-renouvele']);
  });
});
