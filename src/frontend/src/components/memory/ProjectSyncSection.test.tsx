/**
 * Le parcours « Dossier synchronisé » : attacher, préparer, appliquer.
 *
 * Le contrat montré à l'utilisateur : rien ne s'applique sans un plan
 * affiché, les conflits sont annoncés comme non exécutés, un échec de plan
 * (montage débranché) affiche l'erreur - jamais un plan vide de retrait.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  etatSync: vi.fn(),
  definirRacineSync: vi.fn(),
  retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(),
  appliquerPlanSync: vi.fn(),
  journalSync: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { ProjectSyncSection } from './ProjectSyncSection';

const PLAN = {
  id: 'plan-1', etat: 'propose', generation_racine: 1,
  nb_indexer: 3, nb_reindexer: 1, nb_retirer: 2, nb_conflits: 1, nb_inchanges: 5,
  created_at: '2026-08-24T00:00:00Z',
  operations: [
    { id: 'op-1', type: 'indexer', chemin: '/r/a.txt', etat: 'a_faire',
      erreur: null, attempt_count: 0, last_attempt_at: null },
  ],
};

describe('ProjectSyncSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.etatSync.mockResolvedValue({ racine: null, generation: null, dernier_plan: null });
  });

  it('attache un dossier puis affiche la racine', async () => {
    apiMocks.definirRacineSync.mockResolvedValue({ racine: '/r', generation: 1 });

    render(<ProjectSyncSection projectId="p-1" />);
    const champ = await screen.findByLabelText('Chemin du dossier à synchroniser');

    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    fireEvent.change(champ, { target: { value: '/r' } });
    fireEvent.click(screen.getByRole('button', { name: 'Attacher' }));

    await waitFor(() => {
      expect(apiMocks.definirRacineSync).toHaveBeenCalledWith('p-1', '/r');
      expect(screen.getByText('/r')).toBeInTheDocument();
    });
  });

  it('montre le plan avant tout apply, conflits annoncés non exécutés', async () => {
    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    apiMocks.preparerPlanSync.mockResolvedValue(PLAN);

    render(<ProjectSyncSection projectId="p-1" />);
    fireEvent.click(
      await screen.findByRole('button', { name: /Préparer la synchronisation/ }),
    );

    await waitFor(() => {
      expect(screen.getByTestId('sync-plan')).toHaveTextContent(
        '3 à indexer, 1 à réindexer, 2 à retirer, 5 inchangés',
      );
      expect(screen.getByTestId('sync-plan')).toHaveTextContent(
        '1 en conflit (non exécutés)',
      );
    });

    fireEvent.click(screen.getByRole('button', { name: /Appliquer/ }));
    await waitFor(() => {
      expect(apiMocks.appliquerPlanSync).toHaveBeenCalledWith('p-1', 'plan-1');
    });
  });

  it('un plan en échec affiche la cause, jamais un plan vide', async () => {
    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null });
    apiMocks.preparerPlanSync.mockRejectedValue(
      new Error('Aucun plan produit : racine introuvable'),
    );

    render(<ProjectSyncSection projectId="p-1" />);
    fireEvent.click(
      await screen.findByRole('button', { name: /Préparer la synchronisation/ }),
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('racine introuvable');
      expect(screen.queryByTestId('sync-plan')).not.toBeInTheDocument();
    });
  });
});
