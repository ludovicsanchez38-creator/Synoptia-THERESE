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

  it('B-1085 : la commande de secours vise le vrai nom de l’application (THERESE.app)', async () => {
    // Audit bêta 27/10 : la commande n'est proposée que sous macOS.
    Object.defineProperty(window.navigator, 'platform', { value: 'MacIntel', configurable: true });
    vi.mocked(fetch).mockImplementation(() => new Promise<Response>(() => {}));
    const { container } = render(<SplashScreen onReady={vi.fn()} />);
    await waitFor(() => expect(harness.sidecarErrorHandler).not.toBeNull());
    act(() => {
      harness.sidecarErrorHandler?.({ payload: 'Le processus sidecar a quitté' });
    });
    await waitFor(() => expect(container.textContent).toContain('xattr -cr /Applications/THERESE.app'));
    expect(container.textContent).not.toContain('THÉRÈSE.app');
  });
});

it('B-1053 : les pistes suivent le thème, sans texte découpé dans un dégradé', async () => {
  harness.sidecarErrorHandler = null;
  vi.mocked(fetch).mockImplementation(() => new Promise<Response>(() => {}));
  const { container } = render(<SplashScreen onReady={vi.fn()} />);
  const anneau = container.querySelector('[role="status"]') as HTMLElement;
  expect(anneau).toHaveClass('border-border');
  expect(container.querySelector('[class*="bg-white/10"]')).toBeNull();
  expect(container.querySelector('.bg-clip-text')).toBeNull();
  await waitFor(() => expect(harness.sidecarErrorHandler).not.toBeNull());
});
it('B-1055 : progression, étape et erreur fatale sont annoncées', async () => {
  harness.sidecarErrorHandler = null;
  vi.mocked(fetch).mockImplementation(() => new Promise<Response>(() => {}));
  const { container } = render(<SplashScreen onReady={vi.fn()} />);
  expect(container.querySelector('[role="progressbar"]')).toHaveAttribute('aria-valuenow');
  expect(container.querySelector('[aria-live="polite"]')).not.toBeNull();
  await waitFor(() => expect(harness.sidecarErrorHandler).not.toBeNull());
  act(() => harness.sidecarErrorHandler?.({ payload: 'Échec factice du moteur' }));
  expect(container.querySelector('[role="alert"]')).not.toBeNull();
});

it('B-1155 : un échec de résolution du port affiche une erreur et arrête le démarrage', async () => {
  vi.mocked(fetch).mockClear();
  harness.initApiBase.mockRejectedValueOnce(new Error('IPC indisponible'));
  const onReady = vi.fn();
  const { container } = render(<SplashScreen onReady={onReady} />);
  await waitFor(() => expect(container.querySelector('[role="alert"]')).toHaveTextContent(
    "Impossible de joindre le moteur. Relance THÉRÈSE.",
  ));
  expect(fetch).not.toHaveBeenCalled();
  expect(onReady).not.toHaveBeenCalled();
});

it.each([
  new Error('Connexion interrompue'), new TypeError('Port illisible'),
  new DOMException('Pont fermé', 'NetworkError'), 'Moteur absent',
  null, undefined, 42, { code: 'IPC_INDISPONIBLE' },
])('B-1155 : rejet de forme variable (%s)', async (raison) => {
  vi.mocked(fetch).mockClear();
  harness.initApiBase.mockRejectedValueOnce(raison);
  const onReady = vi.fn();
  const { container } = render(<SplashScreen onReady={onReady} />);
  await waitFor(() => expect(container.querySelector('[role="alert"]')).toHaveTextContent(
    'Impossible de joindre le moteur. Relance THÉRÈSE.',
  ));
  expect(fetch).not.toHaveBeenCalled();
  expect(onReady).not.toHaveBeenCalled();
});

it.each([false, true])('B-1155 : rejet différé, démontage=%s', async (demonter) => {
  vi.mocked(fetch).mockClear();
  let rejeter!: (raison: unknown) => void;
  harness.initApiBase.mockImplementationOnce(() => new Promise<void>((_resolve, reject) => {
    rejeter = reject;
  }));
  const onReady = vi.fn();
  const { container, unmount } = render(<SplashScreen onReady={onReady} />);
  if (demonter) unmount();
  await act(async () => rejeter('Échec différé'));
  if (demonter) {
    expect(container).toBeEmptyDOMElement();
  } else {
    expect(container.querySelector('[role="alert"]')).toHaveTextContent(
      'Impossible de joindre le moteur. Relance THÉRÈSE.',
    );
  }
  expect(fetch).not.toHaveBeenCalled();
  expect(onReady).not.toHaveBeenCalled();
});
