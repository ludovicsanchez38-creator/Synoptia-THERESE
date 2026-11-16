import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

type Handler = (event: { payload: unknown }) => void;
const pont = vi.hoisted(() => ({
  invoke: vi.fn(),
  handlers: {} as Record<string, Handler>,
}));
vi.mock('@tauri-apps/api/core', () => ({ invoke: pont.invoke }));
vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn((name: string, handler: Handler) => {
    pont.handlers[name] = handler;
    return Promise.resolve(() => { delete pont.handlers[name]; });
  }),
}));
vi.mock('@tauri-apps/api/app', () => ({ getVersion: vi.fn().mockResolvedValue('0.83.0') }));
vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ setProgressBar: vi.fn().mockResolvedValue(undefined) }),
  ProgressBarStatus: { None: 'none', Normal: 'normal' },
}));

beforeEach(() => {
  vi.resetModules();
  vi.useFakeTimers();
  vi.stubEnv('VITE_THERESE_BACKEND_PORT', '9');
  pont.invoke.mockReset().mockResolvedValue(0);
  pont.handlers = {};
  vi.mocked(fetch).mockReset().mockImplementation(async (url) =>
    new Response(JSON.stringify({ status: 'healthy', version: '0.83.0' }), {
      status: String(url) === 'http://127.0.0.1:29147/health' ? 200 : 503,
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllEnvs();
});

it.each(['sondage', 'bouton de relance'])('R1-1 : retrouve le port après un repli depuis le %s du splash', async (reprise) => {
  // Le vrai initApiBase est exercé, seuls IPC et HTTP sont doublés.
  const { SplashScreen } = await import('./SplashScreen');
  const onReady = vi.fn();
  render(<SplashScreen onReady={onReady} />);
  await act(async () => {
    await vi.dynamicImportSettled();
    await vi.advanceTimersByTimeAsync(3_100);
  });
  expect(pont.invoke.mock.calls.filter(([commande]) => commande === 'get_backend_port')).toHaveLength(11);
  expect(onReady).not.toHaveBeenCalled();

  if (reprise === 'bouton de relance') {
    act(() => pont.handlers['sidecar-status']({ payload: { state: 'failed' } }));
  }
  pont.invoke.mockImplementation(async (commande) => commande === 'get_backend_port' ? 29147 : undefined);
  if (reprise === 'bouton de relance') {
    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));
  }
  await act(async () => {
    await vi.dynamicImportSettled();
    await vi.advanceTimersByTimeAsync(2_400);
  });

  expect(onReady).toHaveBeenCalledTimes(1);
  expect(vi.mocked(fetch).mock.calls.at(-1)?.[0]).toBe('http://127.0.0.1:29147/health');
  expect(pont.invoke.mock.calls.filter(([commande]) => commande === 'get_backend_port')).toHaveLength(12);
});
