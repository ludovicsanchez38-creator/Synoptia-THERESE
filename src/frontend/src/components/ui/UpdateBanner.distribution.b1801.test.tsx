import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const doubles = vi.hoisted(() => ({ getBundleType: vi.fn(), invoke: vi.fn(), check: vi.fn() }));
vi.mock('@tauri-apps/api/app', () => ({ getBundleType: doubles.getBundleType }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: doubles.invoke }));
vi.mock('@tauri-apps/plugin-updater', () => ({ check: doubles.check }));
import { UpdateBanner } from './UpdateBanner';

describe('B-1801 : la distribution Linux doit aussi autoriser la mise à jour', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.stubGlobal('__TAURI__', {});
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue('Linux x86_64');
    // Un binaire issu du .deb peut être extrait ou repaqueté sous Manjaro.
    doubles.getBundleType.mockResolvedValue('deb');
    doubles.check.mockResolvedValue({ available: true, version: '0.84.0' });
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it.each(['Manjaro', 'Fedora', 'distribution inconnue'])('%s : propose seulement le téléchargement manuel', async () => {
    doubles.invoke.mockResolvedValue({ os: 'linux', linux_debian: false });
    render(<UpdateBanner />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
      await vi.dynamicImportSettled();
    });
    expect(screen.queryByRole('button', { name: 'Installer maintenant' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
    expect(doubles.check).not.toHaveBeenCalled();
  });

  it('une distribution Debian reconnue conserve l’installation du paquet deb', async () => {
    doubles.invoke.mockResolvedValue({ os: 'linux', linux_debian: true });
    render(<UpdateBanner />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
      await vi.dynamicImportSettled();
    });
    expect(screen.getByRole('button', { name: 'Installer maintenant' })).toBeInTheDocument();
    expect(doubles.check).toHaveBeenCalledTimes(1);
  });

  it('R1-6 : le repli manuel ne prétend pas avoir trouvé une nouvelle version', async () => {
    doubles.invoke.mockResolvedValue({ os: 'linux', linux_debian: false });
    doubles.check.mockResolvedValue(null);
    render(<UpdateBanner />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
      await vi.dynamicImportSettled();
    });
    expect(screen.getByRole('status')).not.toHaveTextContent(/nouvelle version/i);
    expect(screen.getByRole('status')).toHaveTextContent(/Impossible de vérifier/);
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toBeInTheDocument();
    expect(doubles.check).not.toHaveBeenCalled();
  });

  it.each(['champ absent', 'lecture impossible'])('%s : conserve le téléchargement manuel', async (cas) => {
    if (cas === 'champ absent') doubles.invoke.mockResolvedValue({ os: 'linux' });
    else doubles.invoke.mockRejectedValue(new Error('Lecture impossible'));
    render(<UpdateBanner />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
      await vi.dynamicImportSettled();
    });
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toBeInTheDocument();
    expect(doubles.check).not.toHaveBeenCalled();
  });

  it('revérifie la distribution au clic avant de télécharger ou d’arrêter le moteur', async () => {
    doubles.invoke.mockResolvedValueOnce({ os: 'linux', linux_debian: true }).mockResolvedValue({ os: 'linux', linux_debian: false });
    const installer = vi.fn();
    doubles.check.mockResolvedValue({ available: true, version: '0.84.0', downloadAndInstall: installer });
    render(<UpdateBanner />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
      await vi.dynamicImportSettled();
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Installer maintenant' }));
      await vi.dynamicImportSettled();
    });
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toBeInTheDocument();
    expect(doubles.check).toHaveBeenCalledTimes(1);
    expect(installer).not.toHaveBeenCalled();
    expect(doubles.invoke.mock.calls).toEqual([['get_system_info'], ['get_system_info']]);
  });
});
