/**
 * B-1037 (ronde B4 du cycle 11, D-B4-4) : en navigateur, sans les API natives,
 * la vue annonce « Les fichiers locaux sont accessibles depuis l'application
 * THÉRÈSE », mais les boutons de la barre restaient actifs : « Répertoire
 * personnel » levait une exception non rattrapée (homeDir sans try),
 * « Actualiser » et « Ouvrir un dossier » écrivaient des TypeError en console.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  getWorkingDirectory: vi.fn(), indexFile: vi.fn(), listFiles: vi.fn().mockResolvedValue([]),
}));
vi.mock('@tauri-apps/api/path', () => ({
  homeDir: vi.fn(() => Promise.reject(new TypeError("Cannot read properties of undefined (reading 'invoke')"))),
  resolve: vi.fn(),
}));
vi.mock('@tauri-apps/plugin-fs', () => ({
  readDir: vi.fn(() => Promise.reject(new TypeError('invoke'))), stat: vi.fn(),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn(() => Promise.reject(new TypeError('invoke'))) }));
vi.mock('../../lib/utils', async () => {
  const actual = await vi.importActual<typeof import('../../lib/utils')>('../../lib/utils');
  return { ...actual, isTauri: () => false };
});

import { FileBrowser } from './FileBrowser';

describe('B-1037 : la vue Fichiers en navigateur ne propose pas de gestes natifs', () => {
  let erreurs: ReturnType<typeof vi.spyOn>;
  beforeEach(() => { erreurs = vi.spyOn(console, 'error').mockImplementation(() => undefined); });
  afterEach(() => { erreurs.mockRestore(); });

  it('les boutons qui exigent l’application native sont désactivés', async () => {
    render(<FileBrowser />);
    expect(await screen.findByText(/accessibles depuis l’application THÉRÈSE/)).toBeInTheDocument();
    for (const nom of ['Répertoire personnel', 'Actualiser', 'Ouvrir un dossier', 'Dossier racine']) {
      expect(screen.getByRole('button', { name: nom })).toBeDisabled();
    }
  });

  it('un clic forcé ne lève rien et n’écrit rien en console', async () => {
    const rejets: unknown[] = [];
    const surRejet = (e: PromiseRejectionEvent) => rejets.push(e.reason);
    window.addEventListener('unhandledrejection', surRejet);
    render(<FileBrowser />);
    await screen.findByText(/accessibles depuis l’application THÉRÈSE/);
    for (const nom of ['Répertoire personnel', 'Actualiser', 'Ouvrir un dossier', 'Dossier racine']) {
      const bouton = screen.getByRole('button', { name: nom });
      bouton.removeAttribute('disabled');
      fireEvent.click(bouton);
    }
    await new Promise((r) => setTimeout(r, 20));
    window.removeEventListener('unhandledrejection', surRejet);
    expect(rejets).toEqual([]);
    expect(erreurs).not.toHaveBeenCalled();
  });
});
