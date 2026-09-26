/**
 * Revue P-148, passe 2, constat 2 : en démonstration, une étiquette de tâche
 * sortait en clair, alors qu'une étiquette peut être un nom de client (la
 * recette du dépôt étiquette un projet « Ruiz »). Quatre endroits : l'annonce
 * des filtres retirés, le sélecteur « Filtrer par étiquette » (déplié
 * d'office par « Voir les tâches » d'un projet), et les cartes des deux
 * dispositions, liste et colonnes. La vue Projets masquait déjà les siennes
 * (ProjectsKanban, maskText).
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { buildReplacementMap, maskText } from '../../lib/demoMask';
import { useDemoStore } from '../../stores/demoStore';
import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), listProjects: vi.fn(), getProject: vi.fn(), listContacts: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, ...api };
});

import { TasksPanel } from './TasksPanel';

const VICTOR = {
  id: 'c-victor', first_name: 'Victor', last_name: 'Ruiz', company: null, email: null, phone: null, address: null,
  notes: null, tags: [], stage: 'contact', score: 0, source: null, last_interaction: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};
const TACHE = {
  id: 't-1', title: 'Métrer la pièce', description: null, status: 'todo', priority: 'medium', due_date: null,
  project_id: 'p-cuisine', contact_id: null, tags: ['Ruiz'],
  created_at: '2026-09-25T10:00:00', updated_at: '2026-09-25T10:00:00', completed_at: null,
};
const REMPLACEMENTS = buildReplacementMap([VICTOR], []);
const PSEUDONYME = maskText('Ruiz', REMPLACEMENTS);

function poser(viewMode: 'list' | 'kanban') {
  useTaskStore.setState({
    tasks: [], currentTaskId: null, isTaskFormOpen: false, viewMode, searchQuery: '',
    filterStatus: null, filterPriority: null, filterProjectId: null, filterTag: null, filtresRetires: null,
  } as never);
}

describe('Revue P-148, passe 2, constat 2 : en démonstration, une étiquette de tâche ne sort jamais en clair', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listTasks.mockResolvedValue([TACHE]);
    api.listProjects.mockResolvedValue([]);
    api.getProject.mockResolvedValue({ id: 'p-cuisine', name: 'Cuisine' });
    api.listContacts.mockResolvedValue([VICTOR]);
    useDemoStore.setState({ enabled: true, replacementMap: new Map(REMPLACEMENTS) });
    expect(PSEUDONYME).not.toMatch(/Ruiz/);
  });
  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it.each(['list', 'kanban'] as const)('carte de tâche (disposition %s)', async (disposition) => {
    poser(disposition);
    const { container } = render(<TasksPanel standalone />);
    await screen.findByText(PSEUDONYME);
    expect(container.textContent).not.toMatch(/Ruiz/);
  });

  it('sélecteur « Filtrer par étiquette » : le libellé est masqué, le filtre porte toujours sur la vraie étiquette', async () => {
    poser('list');
    render(<TasksPanel standalone />);
    await screen.findByText(PSEUDONYME);
    fireEvent.click(screen.getByRole('button', { name: 'Filtrer les tâches' }));
    const menu = screen.getByRole('combobox', { name: 'Filtrer par étiquette' });
    const libelles = Array.from(menu.querySelectorAll('option')).map((o) => o.textContent ?? '');
    expect(libelles).toContain(PSEUDONYME);
    expect(libelles.join(' ')).not.toMatch(/Ruiz/);
    fireEvent.change(menu, { target: { value: 'Ruiz' } });
    expect(useTaskStore.getState().filterTag).toBe('Ruiz');
    expect((menu as HTMLSelectElement).selectedOptions[0]).toHaveTextContent(PSEUDONYME);
  });

  it('annonce des filtres retirés (étiquette et recherche, deux textes saisis)', async () => {
    poser('list');
    const { container } = render(<TasksPanel standalone />);
    await screen.findByText(PSEUDONYME);
    act(() => {
      useTaskStore.getState().setFilterTag('Ruiz');
      useTaskStore.getState().setSearchQuery('Ruiz');
    });
    act(() => { useTaskStore.getState().ouvrirSurLeProjet('p-cuisine'); });
    await waitFor(() => expect(screen.getByText(/Filtres précédents retirés/))
      .toHaveTextContent(`Filtres précédents retirés : étiquette « ${PSEUDONYME} », recherche « ${PSEUDONYME} ».`));
    expect(container.textContent).not.toMatch(/Ruiz/);
  });
});
