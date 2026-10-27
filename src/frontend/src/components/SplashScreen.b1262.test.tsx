/**
 * B-1262 : un moteur qui plante au démarrage ne laisse plus le splash promettre
 * « Presque prêt » pendant dix minutes.
 *
 * Rust relance le moteur trois fois puis émet `sidecar-status` « failed ». Le
 * splash n'écoutait que `sidecar-error` (échec de lancement), et le seul
 * porteur du bouton « Relancer le moteur local » n'est monté qu'après le
 * démarrage : l'échec était perdu, le splash sondait un port vide jusqu'à
 * TIMEOUT_MS. Audit bêta du 27/10 : la commande de secours macOS
 * (`xattr -cr`) s'affichait aussi sous Windows.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type Handler = (event: { payload: unknown }) => void;

const harness = vi.hoisted(() => ({
  getApiBase: vi.fn(() => 'http://127.0.0.1:17293'),
  getVersion: vi.fn().mockResolvedValue('0.81.2'),
  initApiBase: vi.fn().mockResolvedValue(undefined),
  invoke: vi.fn().mockResolvedValue(undefined),
  handlers: {} as Record<string, Handler>,
}));

vi.mock('../services/api/core', () => ({
  getApiBase: harness.getApiBase,
  initApiBase: harness.initApiBase,
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn((name: string, handler: Handler) => {
    harness.handlers[name] = handler;
    return Promise.resolve(() => {
      delete harness.handlers[name];
    });
  }),
}));

vi.mock('@tauri-apps/api/core', () => ({ invoke: harness.invoke }));

vi.mock('@tauri-apps/api/app', () => ({ getVersion: harness.getVersion }));

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ setProgressBar: vi.fn().mockResolvedValue(undefined) }),
  ProgressBarStatus: { None: 'none', Normal: 'normal' },
}));

import { SplashScreen } from './SplashScreen';

// Plus long que l'intervalle de sondage du splash (2 s) : la boucle d'attente
// a fait un tour et constaté l'état, le test ne gagne pas la course.
const UN_TOUR_DE_SONDAGE = 2_600;
const attendre = (ms: number) => new Promise((r) => setTimeout(r, ms));

const SAIN = {
  ok: true,
  status: 200,
  text: () => Promise.resolve(JSON.stringify({ status: 'healthy', version: '0.81.2' })),
} as unknown as Response;

function plateforme(valeur: string) {
  Object.defineProperty(window.navigator, 'platform', { value: valeur, configurable: true });
}

async function monter(onReady = vi.fn()) {
  vi.mocked(fetch).mockImplementation(() => Promise.reject(new TypeError('connexion refusée')));
  const rendu = render(<SplashScreen onReady={onReady} />);
  await waitFor(() => {
    expect(harness.handlers['sidecar-status']).toBeDefined();
    expect(fetch).toHaveBeenCalled();
  });
  return { ...rendu, onReady };
}

describe('B-1262 - le splash entend l’abandon du moteur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    harness.handlers = {};
    harness.invoke.mockResolvedValue(undefined);
    plateforme('MacIntel');
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('« failed » arrête l’attente et montre l’échec avec le bouton de relance', async () => {
    const { onReady } = await monter();

    act(() => harness.handlers['sidecar-status']({ payload: { state: 'failed', attempt: 3 } }));

    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent(/s’est arrêté au démarrage/);
    expect(screen.getByRole('button', { name: 'Relancer le moteur local' })).toBeInTheDocument();
    expect(screen.queryByText(/Presque prêt/)).toBeNull();

    const appels = vi.mocked(fetch).mock.calls.length;
    vi.useFakeTimers();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(vi.mocked(fetch).mock.calls.length).toBe(appels);
    expect(onReady).not.toHaveBeenCalled();
  });

  it('le bouton relance le moteur puis reprend l’attente jusqu’au démarrage', async () => {
    const { onReady } = await monter();
    act(() => harness.handlers['sidecar-status']({ payload: { state: 'failed', attempt: 3 } }));
    await screen.findByRole('alert');
    // La première attente est terminée : seule une nouvelle peut aboutir.
    await act(() => attendre(UN_TOUR_DE_SONDAGE));

    vi.mocked(fetch).mockResolvedValue(SAIN);
    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));

    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    await waitFor(() => expect(onReady).toHaveBeenCalledTimes(1), { timeout: 4_000 });
  }, 12_000);

  it('une relance refusée revient sur l’échec, sans attente infinie', async () => {
    await monter();
    act(() => harness.handlers['sidecar-status']({ payload: { state: 'failed', attempt: 3 } }));
    await screen.findByRole('alert');
    harness.invoke.mockRejectedValueOnce(new Error('relance impossible'));

    fireEvent.click(screen.getByRole('button', { name: 'Relancer le moteur local' }));

    await waitFor(() => expect(harness.invoke).toHaveBeenCalledWith('restart_backend'));
    expect(await screen.findByRole('button', { name: 'Relancer le moteur local' })).toBeInTheDocument();
  });

  it('« restarting » est annoncé pendant l’attente', async () => {
    await monter();

    act(() => harness.handlers['sidecar-status']({ payload: { state: 'restarting', attempt: 2 } }));

    await waitFor(() => expect(screen.getByText(/redémarre \(tentative 2\/3\)/)).toBeInTheDocument());
    // Le tour de sondage suivant ne doit pas l'effacer au profit d'un message de progression.
    await act(() => attendre(UN_TOUR_DE_SONDAGE));
    expect(screen.getByText(/redémarre \(tentative 2\/3\)/)).toBeInTheDocument();
  }, 10_000);

  it('« running » rend la main aux messages de progression', async () => {
    await monter();
    act(() => harness.handlers['sidecar-status']({ payload: { state: 'restarting', attempt: 1 } }));
    await waitFor(() => expect(screen.getByText(/redémarre/)).toBeInTheDocument());

    act(() => harness.handlers['sidecar-status']({ payload: { state: 'running', attempt: 0 } }));

    await waitFor(() => expect(screen.queryByText(/redémarre/)).toBeNull(), { timeout: 4_000 });
  });

  it.each([
    [0, false], [-1, false], ['2', false], [Number.NaN, false], [null, false], [undefined, false],
    [1, true], [3, true],
  ])('tentative %s : numéro affiché = %s, jamais de texte incohérent', async (tentative, affiche) => {
    await monter();
    act(() => harness.handlers['sidecar-status']({ payload: { state: 'restarting', attempt: tentative } }));
    await waitFor(() => expect(screen.getByText(/redémarre/)).toBeInTheDocument());
    expect(screen.queryByText(/tentative/) !== null).toBe(affiche);
    expect(screen.queryByText(/NaN|undefined|null|-1/)).toBeNull();
  });

  it('un « failed » arrivé après l’abandon d’un démontage ne fait rien', async () => {
    const { unmount, container } = await monter();
    const statut = harness.handlers['sidecar-status'];
    unmount();
    act(() => statut({ payload: { state: 'failed', attempt: 3 } }));
    expect(container).toBeEmptyDOMElement();
  });

  it.each([
    [{ state: 'failed' }], [{ state: 'inconnu', attempt: 1 }], [null], ['failed'], [{}],
  ])('une charge inattendue (%j) ne casse pas le splash', async (charge) => {
    await monter();
    act(() => harness.handlers['sidecar-status']({ payload: charge }));
    expect(screen.getAllByText(/THÉRÈSE/).length).toBeGreaterThan(0);
  });
});

describe('Audit bêta : la commande de secours suit le système', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    harness.handlers = {};
  });

  it('sous Windows, pas de commande macOS', async () => {
    plateforme('Win32');
    await monter();
    act(() => harness.handlers['sidecar-error']({ payload: 'Le processus sidecar a quitté' }));
    const alerte = await screen.findByRole('alert');
    expect(alerte).not.toHaveTextContent('xattr');
    expect(alerte).toHaveTextContent('Le processus sidecar a quitté');
  });

  it('sous macOS, la commande de secours reste proposée', async () => {
    plateforme('MacIntel');
    await monter();
    act(() => harness.handlers['sidecar-error']({ payload: 'Le processus sidecar a quitté' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('xattr -cr /Applications/THERESE.app');
  });
});
