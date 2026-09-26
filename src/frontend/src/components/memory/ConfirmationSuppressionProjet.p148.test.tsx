/**
 * P-148, lot 4 : la suppression d'un projet dit ce qu'elle emporte.
 *
 * Constat 8 de la revue : une seule confirmation, nourrie par la route
 * d'ensemble, dans la fenêtre du projet ET dans la vue Projets (la carte du
 * Kanban avait la sienne, « Cette action est définitive »). Constat 9 : elle
 * dit aussi ce qui repasse au périmètre général et le planning qui part.
 * Constat 17 : la phrase des totaux, arrivée après la question, s'annonce
 * dans une région `role="status"`.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { EnsembleDuProjet, Project } from '../../services/api';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(), deleteProject: vi.fn(), updateProject: vi.fn(), createProject: vi.fn(),
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
  lireLEnsembleDuProjet: vi.fn(),
}));
vi.mock('../../services/api', () => api);
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listDeliverables: vi.fn().mockResolvedValue([]),
  createDeliverable: vi.fn(),
}));

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ProjectModal } from './ProjectModal';
import { ProjectsPanel } from './ProjectsPanel';

const PROJET: Project = {
  id: 'p-cuisine', name: 'Cuisine Roux', description: null, contact_id: null, status: 'active',
  budget: null, notes: null, tags: null, created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-20T10:00:00Z',
};

function ensemble(partiel: Partial<EnsembleDuProjet> = {}): EnsembleDuProjet {
  return {
    conversations: { total: 7, elements: [] },
    documents: { total: 2, elements: [] },
    taches: { total: 9, ouvertes: 4, en_retard: 1, elements: [] },
    contacts: { total: 2, ranges: 2, elements: [] },
    livrables: { total: 3 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 }, rendez_vous: { total: 2 }, dossier_synchronise: { rattache: false },
    sous_dossiers: { total: 1 }, planning: { total: 1, ressources: 0, calculs: 1 },
    indisponibles: [],
    ...partiel,
  };
}

type Hote = 'fenêtre du projet' | 'vue Projets';

/** Ouvre la confirmation et rend son bloc (la question, les conséquences, les boutons). */
async function demanderLaSuppression(hote: Hote): Promise<HTMLElement> {
  if (hote === 'fenêtre du projet') {
    await act(async () => { render(<ProjectModal isOpen onClose={vi.fn()} project={PROJET} />); });
    const supprimer = screen.getByRole('button', { name: /^Supprimer$/ });
    await act(async () => { fireEvent.click(supprimer); });
    const question = screen.getByText('Supprimer ce projet ?');
    return question.closest('div')?.parentElement as HTMLElement;
  }
  await act(async () => { render(<ProjectsPanel />); });
  await act(async () => { fireEvent.click(await screen.findByRole('button', { name: `Supprimer ${PROJET.name}` })); });
  return screen.getByRole('dialog', { name: 'Supprimer ce projet ?' });
}

describe.each<Hote>(['fenêtre du projet', 'vue Projets'])('P-148 : la confirmation de suppression, depuis la %s', (hote) => {
  beforeEach(() => {
    _clearEscapeHandlers();
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue([PROJET]);
    api.deleteProject.mockResolvedValue(undefined);
    api.listContacts.mockResolvedValue([]);
    api.listProjectFiles.mockResolvedValue({ files: [], total: 0, truncated: false });
    api.etatSync.mockResolvedValue(null);
    api.lireLEnsembleDuProjet.mockResolvedValue(ensemble());
  });
  afterEach(() => { cleanup(); _clearEscapeHandlers(); });

  it('écrit les familles non nulles, omet les autres, et l’annonce dans une région de statut', async () => {
    const bloc = await demanderLaSuppression(hote);
    expect(bloc).toHaveTextContent(`« ${PROJET.name} » sera supprimé.`);
    const statut = within(bloc).getByRole('status');
    await waitFor(() => expect(statut).toHaveTextContent('La suppression emporte 9 tâches, 3 livrables et son planning calculé.'));
    expect(statut).toHaveTextContent('7 conversations, 2 documents et 2 rendez-vous restent, sans lien avec le projet.');
    expect(statut).toHaveTextContent('Ces conversations ne liront plus que les documents généraux.');
    expect(statut).toHaveTextContent('2 contacts et 1 sous-projet rangés dans ce projet passent en Global');
    expect(statut).not.toHaveTextContent(/fichier/);
    // La lecture a lieu à la demande de suppression, pour le compte du moment.
    expect(api.lireLEnsembleDuProjet).toHaveBeenLastCalledWith(PROJET.id, 1);
  });

  it('une lecture en panne laisse la mise en garde générale, jamais un « 0 tâche » inventé', async () => {
    api.lireLEnsembleDuProjet.mockRejectedValue(new Error('réseau'));
    const bloc = await demanderLaSuppression(hote);
    await waitFor(() => expect(within(bloc).getByRole('status')).not.toHaveTextContent(/Lecture/));
    expect(bloc).toHaveTextContent('Cette action est irréversible.');
    expect(bloc).not.toHaveTextContent(/\b0 /);
    expect(bloc).not.toHaveTextContent(/emporte/);
  });

  it('une famille illisible fait taire la liste plutôt que de mentir', async () => {
    api.lireLEnsembleDuProjet.mockResolvedValue(ensemble({ taches: null, indisponibles: ['taches'] }));
    const bloc = await demanderLaSuppression(hote);
    await waitFor(() => expect(within(bloc).getByRole('status')).not.toHaveTextContent(/Lecture/));
    expect(bloc).toHaveTextContent('Cette action est irréversible.');
    expect(bloc).not.toHaveTextContent(/livrables/);
    expect(bloc).not.toHaveTextContent(/\b0 /);
    expect(bloc).not.toHaveTextContent(/emporte/);
  });

  it('recette : les boutons ont leur propre ligne, la phrase garde toute la largeur', async () => {
    const bloc = await demanderLaSuppression(hote);
    const boutons = within(bloc).getByRole('button', { name: 'Annuler' }).parentElement as HTMLElement;
    expect(boutons.className).toMatch(/\b(w-full|basis-full)\b/);
  });

  it('recette : la phrase arrivée, les boutons repoussés sont ramenés dans la vue', async () => {
    const original = Element.prototype.scrollIntoView;
    const defilement = vi.fn();
    Element.prototype.scrollIntoView = defilement;
    try {
      const bloc = await demanderLaSuppression(hote);
      const boutons = within(bloc).getByRole('button', { name: 'Annuler' }).parentElement as HTMLElement;
      await waitFor(() => expect(within(bloc).getByRole('status')).toHaveTextContent('La suppression emporte'));
      await waitFor(() => expect(defilement.mock.contexts).toContain(boutons));
    } finally {
      Element.prototype.scrollIntoView = original;
    }
  });

  it('« Supprimer » supprime le projet', async () => {
    const bloc = await demanderLaSuppression(hote);
    await act(async () => { fireEvent.click(within(bloc).getByRole('button', { name: 'Supprimer' })); });
    await waitFor(() => expect(api.deleteProject).toHaveBeenCalledWith(PROJET.id));
  });
});
