/** B-934 : un état inconnu ne doit pas être présenté comme un projet sans dossier. */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProjectSyncSection } from './ProjectSyncSection';

const api = vi.hoisted(() => ({
  etatSync: vi.fn(),
  definirRacineSync: vi.fn(),
  retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(),
  appliquerPlanSync: vi.fn(),
  journalSync: vi.fn(),
}));

vi.mock('../../services/api', () => api);

describe('B-934 : chargement initial du dossier synchronisé', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
  });

  afterEach(cleanup);

  it('propose une attache quand le serveur confirme qu’aucun dossier n’est lié', async () => {
    api.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });

    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });

    expect(api.etatSync).toHaveBeenCalledWith('projet-c10');
    expect(screen.getByLabelText('Chemin du dossier à synchroniser')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Attacher' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('montre le dossier existant quand sa lecture réussit', async () => {
    api.etatSync.mockResolvedValue({
      racine: '/Documents/projet-c10', generation: 1, dernier_plan: null,
    });

    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });

    expect(screen.getByText('/Documents/projet-c10')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Délier le dossier' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Attacher' })).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('attend la réponse avant de proposer de remplacer un dossier peut-être existant', async () => {
    api.etatSync.mockReturnValue(new Promise(() => {}));

    render(<ProjectSyncSection projectId="projet-c10" />);

    expect(api.etatSync).toHaveBeenCalledWith('projet-c10');
    expect.soft(screen.queryByRole('button', { name: 'Attacher' })).not.toBeInTheDocument();
    expect.soft(screen.queryByLabelText('Chemin du dossier à synchroniser')).not.toBeInTheDocument();
    expect.soft(screen.queryByRole('status')).toBeInTheDocument();
  });

  it('signale l’échec de lecture initiale et propose de réessayer sans formulaire d’attache', async () => {
    api.etatSync.mockRejectedValue(new Error('Le serveur est momentanément indisponible.'));

    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });

    expect(api.etatSync).toHaveBeenCalledTimes(1);
    expect.soft(screen.queryByRole('alert')).toBeInTheDocument();
    expect.soft(screen.queryByRole('button', { name: /réessayer/i })).toBeInTheDocument();
    expect.soft(screen.queryByRole('button', { name: 'Attacher' })).not.toBeInTheDocument();
    expect.soft(screen.queryByLabelText('Chemin du dossier à synchroniser')).not.toBeInTheDocument();
    expect(api.definirRacineSync).not.toHaveBeenCalled();
  });

  it('retrouve le vrai dossier au clic sur Réessayer après un échec initial', async () => {
    api.etatSync.mockRejectedValueOnce(new Error('Connexion interrompue'))
      .mockResolvedValue({ racine: '/Documents/retrouve', generation: 1, dernier_plan: null });
    await act(async () => { render(<ProjectSyncSection projectId="projet-c10" />); });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /réessayer/i })); });

    expect(screen.getByText('/Documents/retrouve')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Attacher' })).toBeNull();
    expect(api.etatSync).toHaveBeenCalledTimes(2);
  });

  it('n’affiche pas la réponse initiale d’un projet quitté entre-temps', async () => {
    let terminer!: (etat: { racine: string; generation: number; dernier_plan: null }) => void;
    api.etatSync.mockReturnValueOnce(new Promise((resolve) => { terminer = resolve; }))
      .mockResolvedValue({ racine: '/Documents/projet-b', generation: 1, dernier_plan: null });
    const { rerender } = render(<ProjectSyncSection projectId="projet-a" />);
    await act(async () => { rerender(<ProjectSyncSection projectId="projet-b" />); });
    await act(async () => { terminer({ racine: '/Documents/projet-a', generation: 1, dernier_plan: null }); });

    expect(screen.getByText('/Documents/projet-b')).toBeInTheDocument();
    expect(screen.queryByText('/Documents/projet-a')).toBeNull();
  });
});
