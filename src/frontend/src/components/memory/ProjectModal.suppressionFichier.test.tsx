/**
 * Un fichier joint ne disparaît pas au premier clic.
 *
 * Trouvé le 27/08/2026 pendant l'audit UX : la corbeille d'un fichier joint
 * appelait `api.deleteFile` DIRECTEMENT (ProjectModal.tsx:104). Un clic, le
 * fichier était perdu, sans confirmation ni retour arrière — alors que la
 * suppression du projet, dans la même modale, en demande une.
 *
 * La confirmation retenue est celle que la modale utilise déjà pour le
 * projet : un bandeau EN LIGNE, dans la même couche. Ce choix est délibéré.
 * Le mécanisme commun `requestExternalAction` aurait paru plus élégant, mais
 * il est fail-OPEN par conception (« sans provider, l'action part
 * immédiatement », useExternalActionConfirmation.ts:19-22) et sa boîte n'a
 * ni piège de focus ni gestion d'Échap : superposée à cette modale, elle
 * laisserait Échap fermer celle du dessous. Un bandeau en ligne est
 * fail-closed par construction — l'appel réseau n'existe qu'au clic de
 * confirmation.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockDeleteFile = vi.fn();
const mockListFiles = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    deleteFile: (...args: unknown[]) => mockDeleteFile(...args),
    listProjectFiles: (...args: unknown[]) => mockListFiles(...args),
    listContacts: vi.fn().mockResolvedValue([]),
  };
});

vi.mock('./ProjectSyncSection', () => ({ ProjectSyncSection: () => null }));

import { ProjectModal } from './ProjectModal';

const PROJET = {
  id: 'p1',
  name: 'Refonte du site',
  status: 'active',
  description: '',
  contact_id: null,
  created_at: '2026-08-01T10:00:00Z',
  updated_at: '2026-08-01T10:00:00Z',
} as never;

const FICHIER = {
  id: 'f1',
  name: 'devis-v2.pdf',
  extension: '.pdf',
  size: 12345,
  path: '/tmp/devis-v2.pdf',
} as never;

describe('La suppression d’un fichier joint demande confirmation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDeleteFile.mockResolvedValue(undefined);
    mockListFiles.mockResolvedValue([FICHIER]);
  });

  async function ouvrir() {
    render(<ProjectModal isOpen onClose={vi.fn()} onSaved={vi.fn()} project={PROJET} />);
    await waitFor(() => expect(screen.getByText('devis-v2.pdf')).toBeInTheDocument());
  }

  it('le premier clic sur la corbeille ne supprime rien', async () => {
    await ouvrir();

    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/i }));

    expect(mockDeleteFile).not.toHaveBeenCalled();
  });

  it('le premier clic annonce ce qui va être supprimé, par son nom', async () => {
    await ouvrir();

    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/i }));

    const annonce = await screen.findByText(/Supprimer « devis-v2.pdf » \?/);
    expect(annonce).toBeInTheDocument();
  });

  it('on peut renoncer, et le fichier reste', async () => {
    await ouvrir();
    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/i }));

    fireEvent.click(await screen.findByRole('button', { name: 'Conserver le fichier' }));

    expect(mockDeleteFile).not.toHaveBeenCalled();
    expect(screen.queryByText(/Supprimer « devis-v2.pdf » \?/)).toBeNull();
  });

  /**
   * Régression introduite par la confirmation elle-même, trouvée par la
   * revue. La cible retenue survivait au changement de projet : l'effet de
   * réinitialisation remettait l'erreur et la confirmation du PROJET à zéro,
   * mais pas le fichier visé. On pouvait donc ouvrir le projet A, viser un
   * fichier sans confirmer, passer au projet B, et y voir réapparaître la
   * question — puis supprimer un fichier de A depuis B.
   *
   * Une confirmation qui survit à son contexte est pire que pas de
   * confirmation du tout : elle donne l'accord de l'utilisateur à autre chose
   * que ce qu'il a vu.
   */
  it('changer de projet abandonne la suppression en cours', async () => {
    const { rerender } = render(
      <ProjectModal isOpen onClose={vi.fn()} onSaved={vi.fn()} project={PROJET} />,
    );
    await waitFor(() => expect(screen.getByText('devis-v2.pdf')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/i }));
    await screen.findByText(/Supprimer « devis-v2.pdf » \?/);

    const AUTRE = { ...(PROJET as object), id: 'p2', name: 'Autre projet' } as never;
    rerender(<ProjectModal isOpen onClose={vi.fn()} onSaved={vi.fn()} project={AUTRE} />);

    await waitFor(() =>
      expect(screen.queryByText(/Supprimer « devis-v2.pdf » \?/)).toBeNull(),
    );
    expect(mockDeleteFile).not.toHaveBeenCalled();
  });

  it('la suppression n’a lieu qu’après confirmation explicite', async () => {
    await ouvrir();
    fireEvent.click(screen.getByRole('button', { name: /Supprimer le fichier/i }));

    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer définitivement' }));

    await waitFor(() => expect(mockDeleteFile).toHaveBeenCalledWith('f1'));
  });
});
