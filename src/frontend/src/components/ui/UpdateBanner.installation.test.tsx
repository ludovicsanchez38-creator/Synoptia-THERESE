/** B-1111 : aucune installation automatique Linux hors paquet Debian reconnu. */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const doubles = vi.hoisted(() => ({
  getBundleType: vi.fn(), check: vi.fn(), downloadAndInstall: vi.fn(), invoke: vi.fn(), open: vi.fn(),
}));
vi.mock('@tauri-apps/api/app', () => ({ getBundleType: doubles.getBundleType }));
vi.mock('@tauri-apps/plugin-updater', () => ({ check: doubles.check }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: doubles.invoke }));
vi.mock('@tauri-apps/plugin-shell', () => ({ open: doubles.open }));
vi.mock('../../services/api/core', () => ({ API_BASE: 'http://moteur-invalide.test' }));

import { UpdateBanner } from './UpdateBanner';

async function demarrer() {
  render(<UpdateBanner />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5_000);
    await vi.dynamicImportSettled();
  });
}

async function installer() {
  await act(async () => {
    fireEvent.click(screen.getByTestId('update-install-btn'));
    await vi.dynamicImportSettled();
  });
}

describe('installation des mises à jour', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.stubGlobal('__TAURI__', {});
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue('Linux x86_64');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Moteur simulé arrêté')));
    doubles.getBundleType.mockResolvedValue('appimage');
    doubles.check.mockResolvedValue({ available: true, version: '0.80.0', downloadAndInstall: doubles.downloadAndInstall });
    doubles.downloadAndInstall.mockResolvedValue(undefined);
    doubles.invoke.mockResolvedValue(undefined);
    doubles.open.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('propose un lien manuel sur AppImage, même sans cible updater disponible', async () => {
    doubles.check.mockRejectedValue(new Error('TargetNotFound'));
    await demarrer();
    const lien = screen.getByRole('link', { name: /télécharger/i });
    expect(lien).toHaveAttribute('href', 'https://synoptia.fr/therese/alpha/');
    expect(screen.getByText(/manuellement/i)).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(lien);
      await vi.dynamicImportSettled();
    });
    expect(doubles.open).toHaveBeenCalledWith('https://synoptia.fr/therese/alpha/');
    expect(doubles.check).not.toHaveBeenCalled();
    expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
    expect(doubles.invoke).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('refuse aussi si le type ne peut pas être lu', async () => {
    doubles.getBundleType.mockRejectedValue(new Error('Type inconnu'));
    await demarrer();
    expect(screen.getByRole('link', { name: /télécharger/i })).toBeInTheDocument();
    expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('autorise le paquet Debian reconnu', async () => {
    doubles.getBundleType.mockResolvedValue('deb');
    await demarrer();
    await installer();
    expect(doubles.downloadAndInstall).toHaveBeenCalledTimes(1);
    expect(doubles.invoke).toHaveBeenCalledWith('prepare_backend_shutdown');
    expect(fetch).toHaveBeenCalledWith('http://moteur-invalide.test/api/shutdown', { method: 'POST' });
  });

  // Entrées inventées après le correctif, y compris les autres OS conservés.
  it.each([
    ['Linux x86_64', 'deb', true],
    ['Linux x86_64', 'rpm', false],
    ['Linux x86_64', null, false],
    ['Linux x86_64', undefined, false],
    ['Linux aarch64', 'appimage', false],
    ['Linux x86_64', '', false],
    ['Linux x86_64', 'msi', false],
    ['Win32', 'nsis', true],
    ['Win32', 'msi', true],
    ['MacIntel', 'app', true],
    ['Linux x86_64', 'inconnu', false],
    ['', null, false],
  ])('rejeu %s / %s : automatique=%s', async (plateforme, type, automatique) => {
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue(plateforme);
    doubles.getBundleType.mockResolvedValue(type);
    await demarrer();
    if (automatique) {
      await installer();
      expect(doubles.downloadAndInstall).toHaveBeenCalledTimes(1);
    } else {
      expect(screen.getByRole('link', { name: /télécharger/i })).toHaveAttribute('href', 'https://synoptia.fr/therese/alpha/');
      expect(doubles.check).not.toHaveBeenCalled();
      expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
      expect(doubles.invoke).not.toHaveBeenCalled();
      expect(fetch).not.toHaveBeenCalled();
    }
  });

  it('revérifie au clic et conserve le moteur si le type devient inconnu', async () => {
    doubles.getBundleType.mockResolvedValueOnce('deb').mockResolvedValue(null);
    await demarrer();
    await installer();
    expect(screen.getByRole('link', { name: /télécharger/i })).toBeInTheDocument();
    expect(doubles.check).toHaveBeenCalledTimes(1);
    expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
    expect(doubles.invoke).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('ouvre le lien dans le navigateur si le shell échoue', async () => {
    doubles.open.mockRejectedValue(new Error('Shell indisponible'));
    const navigateur = vi.spyOn(window, 'open').mockReturnValue(null);
    await demarrer();
    await act(async () => {
      fireEvent.click(screen.getByRole('link', { name: /télécharger/i }));
      await vi.dynamicImportSettled();
    });
    expect(navigateur).toHaveBeenCalledWith('https://synoptia.fr/therese/alpha/', '_blank', 'noopener,noreferrer');
    expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
  });

  it('reste inactif hors Tauri', async () => {
    Reflect.deleteProperty(window, '__TAURI__');
    await demarrer();
    expect(screen.queryByTestId('update-banner')).not.toBeInTheDocument();
    expect(doubles.getBundleType).not.toHaveBeenCalled();
    expect(doubles.check).not.toHaveBeenCalled();
  });
});
