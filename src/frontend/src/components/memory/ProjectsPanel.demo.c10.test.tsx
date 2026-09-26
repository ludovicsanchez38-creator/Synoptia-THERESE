/** B-939 : le nom protégé sur la carte ne doit pas ressortir dans sa confirmation. */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Project } from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
import { buildReplacementMap, maskText } from '../../lib/demoMask';
import { ProjectsPanel } from './ProjectsPanel';

// Revue P-148, constat 14 : la confirmation lit la route d'ensemble ; sans
// ce simulacre, elle retombait en silence sur la mise en garde générale et
// la phrase des conséquences n'était jamais rendue en démonstration.
const api = vi.hoisted(() => ({ listProjects: vi.fn(), deleteProject: vi.fn(), lireLEnsembleDuProjet: vi.fn() }));
vi.mock('../../services/api', () => api);
// La confirmation étudiée appartient au panneau. Le formulaire dispose de
// ses propres tests d’intégration, avec ses vrais hooks et sa vraie synchro.
vi.mock('./ProjectModal', () => ({ ProjectModal: () => null }));

const PROJET: Project = {
  id: 'projet-panneau-demo-c10', name: 'Chantier Ardent c10', description: null,
  contact_id: null, status: 'active', budget: null, notes: null, tags: null,
  created_at: '2026-09-22T10:00:00Z', updated_at: '2026-09-22T10:00:00Z',
};
const REMPLACEMENTS = buildReplacementMap([], [PROJET]);
const NOM_DEMO = maskText(PROJET.name, REMPLACEMENTS);

describe('B-939 : confirmation de suppression depuis Projets en mode démo', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue([PROJET]);
    api.deleteProject.mockResolvedValue(undefined);
    api.lireLEnsembleDuProjet.mockResolvedValue({
      conversations: { total: 2, elements: [] }, documents: { total: 1, elements: [] },
      taches: { total: 3, ouvertes: 1, en_retard: 0, elements: [] },
      contacts: { total: 1, ranges: 1, elements: [] }, livrables: { total: 1 },
      fichiers: { total: 1, deposes: 1, indexes_sur_place: 0 }, dossier_synchronise: { rattache: false },
      rendez_vous: { total: 0 }, sous_dossiers: { total: 0 }, planning: { total: 0, ressources: 0, calculs: 0 },
      indisponibles: [],
    });
  });

  it('B-1621 (décision de Ludo, 26/09) : en démonstration, Supprimer n’ouvre pas la confirmation et ne supprime rien', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map(REMPLACEMENTS) });
    render(<ProjectsPanel />);
    fireEvent.click(await screen.findByRole('button', { name: `Supprimer ${NOM_DEMO}` }));
    expect(screen.queryByRole('dialog', { name: 'Supprimer ce projet ?' })).toBeNull();
    expect(api.deleteProject).not.toHaveBeenCalled();
    expect(screen.queryByText(PROJET.name)).toBeNull();
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('nomme normalement le projet lorsque le mode démo est désactivé', async () => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map(REMPLACEMENTS) });
    render(<ProjectsPanel />);
    fireEvent.click(await screen.findByRole('button', { name: `Supprimer ${PROJET.name}` }));
    expect(screen.getByRole('dialog', { name: 'Supprimer ce projet ?' })).toHaveTextContent(PROJET.name);
    expect(api.deleteProject).not.toHaveBeenCalled();
  });
});
