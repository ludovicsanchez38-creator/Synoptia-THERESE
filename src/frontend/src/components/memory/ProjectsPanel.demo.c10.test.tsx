/** B-939 : le nom protégé sur la carte ne doit pas ressortir dans sa confirmation. */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Project } from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
import { buildReplacementMap, maskText } from '../../lib/demoMask';
import { ProjectsPanel } from './ProjectsPanel';

const api = vi.hoisted(() => ({ listProjects: vi.fn(), deleteProject: vi.fn() }));
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
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('nomme normalement le projet lorsque le mode démo est désactivé', async () => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map(REMPLACEMENTS) });
    render(<ProjectsPanel />);
    fireEvent.click(await screen.findByRole('button', { name: `Supprimer ${PROJET.name}` }));
    expect(screen.getByRole('dialog', { name: 'Supprimer le projet ?' })).toHaveTextContent(PROJET.name);
    expect(api.deleteProject).not.toHaveBeenCalled();
  });

  it('garde le nom masqué dans la confirmation et supprime uniquement le vrai identifiant', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map(REMPLACEMENTS) });
    render(<ProjectsPanel />);
    const supprimer = await screen.findByRole('button', { name: `Supprimer ${NOM_DEMO}` });
    expect(screen.queryByText(PROJET.name)).toBeNull();
    fireEvent.click(supprimer);

    const confirmation = screen.getByRole('dialog', { name: 'Supprimer le projet ?' });
    expect.soft(confirmation).not.toHaveTextContent(PROJET.name);
    expect.soft(confirmation).toHaveTextContent(NOM_DEMO);
    expect(api.deleteProject).not.toHaveBeenCalled();
    fireEvent.click(within(confirmation).getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(api.deleteProject).toHaveBeenCalledWith(PROJET.id));
  });
});
