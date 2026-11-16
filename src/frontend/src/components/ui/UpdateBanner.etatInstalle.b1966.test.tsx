import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import type { DownloadEvent } from '@tauri-apps/plugin-updater';
import { UpdateBanner } from './UpdateBanner';

const doubles = vi.hoisted(() => ({ check: vi.fn(), installer: vi.fn(), relaunch: vi.fn() }));
vi.mock('@tauri-apps/api/app', () => ({ getBundleType: vi.fn().mockResolvedValue('app') }));
vi.mock('@tauri-apps/plugin-updater', () => ({ check: doubles.check }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn().mockResolvedValue(undefined) }));
vi.mock('@tauri-apps/plugin-process', () => ({ relaunch: doubles.relaunch }));
vi.mock('../../services/api/core', () => ({ API_BASE: 'http://moteur-fictif.test' }));

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers();
  vi.stubGlobal('__TAURI__', {});
  vi.spyOn(navigator, 'platform', 'get').mockReturnValue('MacIntel');
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Moteur fictif arrêté')));
  doubles.check.mockResolvedValue({ available: true, version: '0.83.1', downloadAndInstall: doubles.installer });
  doubles.installer.mockResolvedValue(undefined);
  doubles.relaunch.mockResolvedValue(undefined);
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function lancerInstallation() {
  render(<UpdateBanner />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5_000);
    await vi.dynamicImportSettled();
  });
  await act(async () => {
    fireEvent.click(screen.getByTestId('update-install-btn'));
    await vi.dynamicImportSettled();
  });
}

it('B-1966 : après installation le bandeau annonce installé et propose de l’appliquer', async () => {
  await lancerInstallation();
  expect(doubles.installer).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('status')).toHaveTextContent('Mise à jour v0.83.1 installée');
  const bouton = screen.getByRole('button', { name: 'Redémarrer pour appliquer' });
  await act(async () => {
    fireEvent.click(bouton);
    await vi.advanceTimersByTimeAsync(1_000);
    await vi.dynamicImportSettled();
  });
  expect(doubles.relaunch).toHaveBeenCalledTimes(1);
  expect(doubles.installer).toHaveBeenCalledTimes(1);
});

it('B-1966 : la fin du téléchargement ne permet pas de redémarrer avant la fin de l’installation', async () => {
  let terminer!: () => void;
  doubles.installer.mockImplementationOnce((evenement: (e: DownloadEvent) => void) => {
    evenement({ event: 'Finished' });
    return new Promise<void>(resolve => { terminer = resolve; });
  });
  await lancerInstallation();
  expect(screen.queryByTestId('update-restart-btn')).not.toBeInTheDocument();
  await act(async () => { terminer(); });
  expect(screen.getByRole('button', { name: 'Redémarrer pour appliquer' })).toBeInTheDocument();
});
