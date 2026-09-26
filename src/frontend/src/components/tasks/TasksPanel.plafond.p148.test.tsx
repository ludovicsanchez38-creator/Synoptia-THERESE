/**
 * Revue P-148, constat 10 : « Voir les N tâches dans Tâches » annonce le
 * total de la route d'ensemble, qui compte sans borne, alors que la vue
 * Tâches lit au plus une page (1 000 tâches, plafond de l'API, demandé
 * explicitement par listTasks). Au plafond, la vue le dit au lieu de laisser
 * croire la liste complète.
 *
 * NB : la revue situait la borne à 200 (défaut de la route) ; le client
 * demande en réalité limit=1000 (services/api/tasks.ts). Le test suit la
 * valeur réelle, exportée par le client.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), listProjects: vi.fn(), listContacts: vi.fn(), getProject: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, ...api };
});
// La liste elle-même n'est pas étudiée ici : mille lignes rendues ne
// prouveraient rien de plus et ralentiraient la suite.
vi.mock('./TaskList', () => ({ TaskList: () => null }));
vi.mock('./TaskKanban', () => ({ TaskKanban: () => null }));

import { PLAFOND_TACHES, listTasks as listTasksReel } from '../../services/api/tasks';
import { TasksPanel } from './TasksPanel';

function taches(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    id: `t-${i}`, title: `Tâche ${i}`, description: null, status: 'todo', priority: 'medium', due_date: null,
    project_id: 'p-cuisine', contact_id: null, tags: [],
    created_at: '2026-09-25T10:00:00', updated_at: '2026-09-25T10:00:00', completed_at: null,
  }));
}

describe('Revue P-148, constat 10 : la vue Tâches dit quand sa liste est incomplète', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listProjects.mockResolvedValue([{ id: 'p-cuisine', name: 'Cuisine Roux' }]);
    api.listContacts.mockResolvedValue([]);
    useTaskStore.setState({
      tasks: [], currentTaskId: null, isTaskFormOpen: false, viewMode: 'list', searchQuery: '',
      filterStatus: null, filterPriority: null, filterProjectId: 'p-cuisine', filterTag: null, filtresRetires: null,
    } as never);
  });
  afterEach(() => cleanup());

  it('au plafond, la liste se dit incomplète', async () => {
    api.listTasks.mockResolvedValue(taches(PLAFOND_TACHES));
    render(<TasksPanel standalone />);
    const annonce = await screen.findByText(/Liste incomplète/);
    // toHaveTextContent replie les espaces du texte rendu (l'espace fine
    // insécable du séparateur de milliers compris), pas ceux de l'attendu.
    const millier = PLAFOND_TACHES.toLocaleString('fr-FR').replace(/\s/g, ' ');
    expect(annonce).toHaveTextContent(`Liste incomplète : seules les ${millier} premières tâches sont chargées.`);
  });

  it('sous le plafond, rien n’est annoncé', async () => {
    api.listTasks.mockResolvedValue(taches(PLAFOND_TACHES - 1));
    render(<TasksPanel standalone />);
    await waitFor(() => expect(api.listTasks).toHaveBeenCalled());
    await waitFor(() => expect(useTaskStore.getState().tasks).toHaveLength(PLAFOND_TACHES - 1));
    expect(screen.queryByText(/Liste incomplète/)).toBeNull();
  });

  it('le client demande bien le plafond à la route', async () => {
    const fetchEspion = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('[]', { status: 200 }));
    try {
      await listTasksReel({ project_id: 'p-cuisine' });
      // D'autres lectures des rendus précédents peuvent encore passer par fetch.
      const url = fetchEspion.mock.calls.map((c) => String(c[0])).find((u) => u.includes('/api/tasks'));
      expect(new URL(url ?? '', 'http://x').searchParams.get('limit')).toBe(String(PLAFOND_TACHES));
    } finally {
      fetchEspion.mockRestore();
    }
  });
});
