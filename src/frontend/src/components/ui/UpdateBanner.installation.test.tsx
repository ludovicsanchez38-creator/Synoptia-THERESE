import { installLocalStorageStub } from '../../test/localStorage-stub';
/** B-1111 : aucune installation automatique Linux hors paquet Debian reconnu. */
import { createServer, get } from 'node:http';
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
    // Le contrat natif fournit désormais la famille de la distribution (B-1801).
    doubles.invoke.mockResolvedValue({ os: 'linux', linux_debian: true });
    doubles.open.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('annonce la 0.84.0 depuis un manifeste local pour une 0.83.0 simulée', async () => {
    const installee = '0.83.0';
    const chemins: string[] = [];
    const serveur = createServer((requete, reponse) => {
      chemins.push(requete.url ?? '');
      reponse.writeHead(200, { 'content-type': 'application/json' });
      reponse.end(JSON.stringify({
        version: '0.84.0',
        notes: 'La 0.84 vient du serveur de test.',
        platforms: {
          'linux-x86_64-deb': { url: 'https://exemple.test/therese-0.84.0.deb', signature: 'factice' },
        },
      }));
    });
    await new Promise<void>((resoudre, rejeter) => {
      serveur.once('error', rejeter);
      serveur.listen(0, '127.0.0.1', resoudre);
    });
    try {
      const adresse = serveur.address();
      if (!adresse || typeof adresse === 'string') throw new Error('Adresse du serveur de test manquante');
      const url = `http://127.0.0.1:${adresse.port}/latest.json`;
      type ManifesteLu = { version: string; notes: string; platforms: Record<string, unknown> };
      let lecture: Promise<ManifesteLu> | undefined;
      doubles.getBundleType.mockResolvedValue('deb');
      doubles.check.mockImplementation(async () => {
        lecture = new Promise((resoudre, rejeter) => {
          get(url, (reponse) => {
            reponse.setEncoding('utf8');
            let contenu = '';
            reponse.on('data', (texte) => { contenu += texte; });
            reponse.on('end', () => {
              try { resoudre(JSON.parse(contenu) as ManifesteLu); }
              catch (erreur) { rejeter(erreur); }
            });
            reponse.on('error', rejeter);
          }).on('error', rejeter);
        });
        const manifeste = await lecture;
        expect(manifeste.platforms).toHaveProperty('linux-x86_64-deb');
        return {
          available: installee === '0.83.0' && manifeste.version === '0.84.0',
          version: manifeste.version,
          body: manifeste.notes,
        };
      });
      await demarrer();
      expect(doubles.check).toHaveBeenCalledTimes(1);
      if (!lecture) throw new Error('Le plugin simulé n’a pas lu le manifeste');
      await act(async () => { await lecture; });
      expect(chemins).toEqual(['/latest.json']);
      expect(screen.getByTestId('update-banner')).toHaveTextContent('0.84.0');
      expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
    } finally {
      await new Promise<void>((resoudre) => { serveur.close(() => resoudre()); });
    }
  });

  it('propose un lien manuel sur AppImage, même sans cible updater disponible', async () => {
    doubles.check.mockRejectedValue(new Error('TargetNotFound'));
    await demarrer();
    const lien = screen.getByRole('link', { name: /télécharger/i });
    expect(lien).toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
    expect(screen.getByText(/manuellement/i)).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(lien);
      await vi.dynamicImportSettled();
    });
    expect(doubles.open).toHaveBeenCalledWith('https://synoptia.fr/therese/beta/');
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
    doubles.invoke.mockResolvedValue({ os: plateforme === 'Win32' ? 'windows' : plateforme === 'MacIntel' ? 'macos' : 'linux', linux_debian: true });
    doubles.getBundleType.mockResolvedValue(type);
    await demarrer();
    if (automatique) {
      await installer();
      expect(doubles.downloadAndInstall).toHaveBeenCalledTimes(1);
    } else {
      expect(screen.getByRole('link', { name: /télécharger/i })).toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
      expect(doubles.check).not.toHaveBeenCalled();
      expect(doubles.downloadAndInstall).not.toHaveBeenCalled();
      // Un paquet MSI exige maintenant la lecture native pour être refusé sous Linux.
      if (type === 'msi') expect(doubles.invoke).toHaveBeenCalledExactlyOnceWith('get_system_info');
      else expect(doubles.invoke).not.toHaveBeenCalled();
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
    // La lecture initiale de la distribution remplace l'ancien « aucun IPC ».
    // L'arrêt du moteur reste interdit : l'unique appel est une lecture.
    expect(doubles.invoke).toHaveBeenCalledExactlyOnceWith('get_system_info');
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
    expect(navigateur).toHaveBeenCalledWith('https://synoptia.fr/therese/beta/', '_blank', 'noopener,noreferrer');
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

describe('T4 : choix de la vérification automatique', () => {
  beforeEach(() => {
    installLocalStorageStub();
    vi.useFakeTimers();
    vi.clearAllMocks();
    localStorage.clear();
    vi.stubGlobal('__TAURI__', {});
    doubles.getBundleType.mockResolvedValue('deb');
    doubles.invoke.mockResolvedValue({ os: 'linux', linux_debian: true });
    doubles.check.mockResolvedValue(null);
  });
  afterEach(() => {
    cleanup();
    localStorage.clear();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });
  it('ne contacte pas le serveur au démarrage ni six heures après si désactivé', async () => {
    localStorage.setItem('therese-auto-update-check', 'false');
    await demarrer();
    await act(async () => { await vi.advanceTimersByTimeAsync(6 * 60 * 60 * 1000); });
    expect(doubles.check).not.toHaveBeenCalled();
  });
  it('relit le choix après une opération asynchrone avant la requête', async () => {
    doubles.getBundleType.mockImplementation(async () => {
      localStorage.setItem('therese-auto-update-check', 'false');
      return 'deb';
    });
    await demarrer();
    expect(doubles.check).not.toHaveBeenCalled();
  });
});
