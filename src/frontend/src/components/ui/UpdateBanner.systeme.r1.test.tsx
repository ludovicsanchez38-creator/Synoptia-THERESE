import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const doubles = vi.hoisted(() => ({ getBundleType: vi.fn(), invoke: vi.fn(), check: vi.fn(), installer: vi.fn() }));
vi.mock('@tauri-apps/api/app', () => ({ getBundleType: doubles.getBundleType }));
vi.mock('@tauri-apps/api/core', () => ({ invoke: doubles.invoke }));
vi.mock('@tauri-apps/plugin-updater', () => ({ check: doubles.check }));
import { UpdateBanner } from './UpdateBanner';

async function demarrer() {
  render(<UpdateBanner />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5_000);
    await vi.dynamicImportSettled();
  });
}

describe('R1-3 : seul le système natif autorise une installation', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.resetAllMocks();
    vi.stubGlobal('__TAURI__', {});
    vi.stubGlobal('fetch', vi.fn());
    doubles.check.mockResolvedValue({ available: true, version: '0.84.0', downloadAndInstall: doubles.installer });
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it.each([
    ['', 'deb', { os: 'linux', linux_debian: false }, false],
    ['Win32', 'deb', { os: 'linux', linux_debian: false }, false],
    ['', 'deb', { linux_debian: true }, false],
    ['Linux x86_64', 'deb', { os: 'inconnu', linux_debian: true }, false],
    ['MacIntel', 'app', null, false],
    ['', 'deb', { os: 'linux', linux_debian: true }, true],
    ['', 'app', { os: 'macos' }, true],
    ['', 'nsis', { os: 'windows' }, true],
    ['', 'msi', { os: 'windows' }, true],
    ['Win32', 'msi', { os: 'linux', linux_debian: true }, false],
  ])('webview=%s, paquet=%s, système=%j : autorisé=%s', async (platform, type, systeme, autorise) => {
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue(platform);
    doubles.getBundleType.mockResolvedValue(type);
    doubles.invoke.mockResolvedValue(systeme);
    await demarrer();
    if (autorise) {
      expect(screen.getByRole('button', { name: 'Installer maintenant' })).toBeInTheDocument();
      expect(doubles.check).toHaveBeenCalledTimes(1);
    } else {
      expect(screen.queryByRole('button', { name: 'Installer maintenant' })).not.toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
      expect(doubles.check).not.toHaveBeenCalled();
    }
    expect(doubles.invoke).toHaveBeenCalledExactlyOnceWith('get_system_info');
    expect(doubles.installer).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('un système devenu inconnu au clic ne télécharge rien et ne coupe pas le moteur', async () => {
    vi.spyOn(navigator, 'platform', 'get').mockReturnValue('Linux x86_64');
    doubles.getBundleType.mockResolvedValue('deb');
    doubles.invoke.mockResolvedValueOnce({ os: 'linux', linux_debian: true }).mockResolvedValue({ linux_debian: true });
    await demarrer();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Installer maintenant' }));
      await vi.dynamicImportSettled();
    });
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE' })).toBeInTheDocument();
    expect(doubles.invoke.mock.calls).toEqual([['get_system_info'], ['get_system_info']]);
    expect(doubles.check).toHaveBeenCalledTimes(1);
    expect(doubles.installer).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });
});
