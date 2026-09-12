import { act, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type SidecarErrorHandler = (event: { payload: string }) => void;

const harness = vi.hoisted(() => ({
  getApiBase: vi.fn(() => 'http://127.0.0.1:17293'),
  getVersion: vi.fn().mockResolvedValue('0.72.0'),
  initApiBase: vi.fn().mockResolvedValue(undefined),
  sidecarErrorHandler: null as SidecarErrorHandler | null,
}));

vi.mock('../services/api/core', () => ({
  getApiBase: harness.getApiBase,
  initApiBase: harness.initApiBase,
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn((name: string, handler: SidecarErrorHandler) => {
    if (name === 'sidecar-error') harness.sidecarErrorHandler = handler;
    return Promise.resolve(() => {
      harness.sidecarErrorHandler = null;
    });
  }),
}));

vi.mock('@tauri-apps/api/app', () => ({
  getVersion: harness.getVersion,
}));

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ setProgressBar: vi.fn().mockResolvedValue(undefined) }),
  ProgressBarStatus: { None: 'none', Normal: 'normal' },
}));

import { SplashScreen } from './SplashScreen';

describe('B-757 - erreur fatale du sidecar au démarrage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    harness.sidecarErrorHandler = null;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('annule le polling en cours, ne relance aucun health check et ne signale jamais ready', async () => {
    let resolveHealth!: (response: Response) => void;
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => {
      resolveHealth = resolve;
    }));
    const onReady = vi.fn();

    render(<SplashScreen onReady={onReady} />);
    await waitFor(() => {
      expect(harness.sidecarErrorHandler).not.toBeNull();
      expect(fetch).toHaveBeenCalledTimes(1);
    });
    vi.useFakeTimers();

    act(() => {
      harness.sidecarErrorHandler?.({ payload: 'Le processus sidecar a quitté' });
    });

    await act(async () => {
      resolveHealth({
        ok: true,
        status: 200,
        text: vi.fn().mockResolvedValue(JSON.stringify({
          status: 'healthy',
          version: '0.72.0',
        })),
      } as unknown as Response);
      await vi.advanceTimersByTimeAsync(2_500);
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(onReady).not.toHaveBeenCalled();
  });
});
