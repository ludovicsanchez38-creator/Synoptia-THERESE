import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type Handler = (event: { payload: unknown }) => void;

const harness = vi.hoisted(() => ({
  handlers: {} as Record<string, Handler>,
  initApiBase: vi.fn(),
  invoke: vi.fn(),
}));

vi.mock('../services/api/core', () => ({
  getApiBase: () => 'http://127.0.0.1:1',
  initApiBase: harness.initApiBase,
}));
vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn((name: string, handler: Handler) => {
    harness.handlers[name] = handler;
    return Promise.resolve(() => { delete harness.handlers[name]; });
  }),
}));
vi.mock('@tauri-apps/api/core', () => ({ invoke: harness.invoke }));
vi.mock('@tauri-apps/api/app', () => ({ getVersion: vi.fn().mockResolvedValue('0.83.0') }));
vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ setProgressBar: vi.fn().mockResolvedValue(undefined) }),
  ProgressBarStatus: { None: 'none', Normal: 'normal' },
}));

import { SplashScreen } from './SplashScreen';

const sain = {
  ok: true,
  status: 200,
  text: () => Promise.resolve(JSON.stringify({ status: 'healthy', version: '0.83.0' })),
} as Response;

describe('B-1912 : reprise après une erreur de démarrage', () => {
  beforeEach(() => {
    harness.handlers = {};
    harness.initApiBase.mockReset().mockResolvedValue(undefined);
    harness.invoke.mockReset().mockResolvedValue(undefined);
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('moteur indisponible')));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it.each(['sidecar', 'résolution du port'])('%s : relance le moteur et reprend le démarrage', async (cause) => {
    if (cause === 'résolution du port') harness.initApiBase.mockRejectedValueOnce(new Error('IPC'));
    const onReady = vi.fn();
    render(<SplashScreen onReady={onReady} />);

    if (cause === 'sidecar') {
      await waitFor(() => expect(harness.handlers['sidecar-error']).toBeDefined());
      act(() => harness.handlers['sidecar-error']({ payload: 'Échec factice' }));
    }
    await screen.findByRole('alert');
    vi.mocked(fetch).mockResolvedValue(sain);
    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));

    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    await waitFor(() => expect(onReady).toHaveBeenCalledTimes(1), { timeout: 4_000 });
    expect(screen.queryByRole('alert')).toBeNull();
    if (cause === 'résolution du port') expect(harness.initApiBase).toHaveBeenCalledTimes(2);
  });

  it('propose encore la relance lorsque la commande échoue', async () => {
    harness.initApiBase.mockRejectedValueOnce(new Error('IPC'));
    harness.invoke.mockRejectedValueOnce(new Error('relance impossible'));
    render(<SplashScreen onReady={vi.fn()} />);
    await screen.findByRole('alert');

    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));

    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    expect(await screen.findByRole('button', { name: 'Relancer le moteur local' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Impossible de relancer le moteur');
  });

  it('conserve une nouvelle erreur reçue pendant la relance', async () => {
    harness.initApiBase.mockRejectedValueOnce(new Error('IPC'));
    let terminer!: () => void;
    harness.invoke.mockImplementationOnce(() => new Promise<void>((resolve) => { terminer = resolve; }));
    const onReady = vi.fn();
    render(<SplashScreen onReady={onReady} />);
    await screen.findByRole('alert');
    await waitFor(() => expect(harness.handlers['sidecar-error']).toBeDefined());

    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));
    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    act(() => harness.handlers['sidecar-error']({ payload: 'Nouvel échec factice' }));
    await act(async () => { terminer(); });

    expect(screen.getByRole('alert')).toHaveTextContent('Nouvel échec factice');
    expect(screen.getByRole('button', { name: 'Relancer le moteur local' })).toBeInTheDocument();
    expect(onReady).not.toHaveBeenCalled();
  });

  it('le dépassement du délai propose également la relance', async () => {
    vi.useFakeTimers();
    let maintenant = 0;
    vi.spyOn(Date, 'now').mockImplementation(() => maintenant);
    await act(async () => { render(<SplashScreen onReady={vi.fn()} />); });
    maintenant = 600_001;
    await act(async () => { await vi.advanceTimersByTimeAsync(2_000); });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Relancer le moteur local' })).toBeInTheDocument();
  });
});
