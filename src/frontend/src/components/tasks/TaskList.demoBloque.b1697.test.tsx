/**
 * B-1697 (suite de B-1621 et B-1689, décision de Ludo du 26/09) : en démo, la
 * liste des tâches terminait ou supprimait la vraie tâche, alors que le
 * kanban le bloque déjà.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), deleteTask: vi.fn(), completeTask: vi.fn(), uncompleteTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => api.listTasks(...a),
  deleteTask: (...a: unknown[]) => api.deleteTask(...a),
  completeTask: (...a: unknown[]) => api.completeTask(...a),
  uncompleteTask: (...a: unknown[]) => api.uncompleteTask(...a),
}));
// Masque neutre : les noms restent lisibles pour viser les boutons.
vi.mock('../../hooks', async () => ({
  ...await vi.importActual<typeof import('../../hooks')>('../../hooks'),
  useDemoMask: () => ({ enabled: true, maskText: (t: string) => t, maskContact: (c: unknown) => c, populateMap: vi.fn() }),
}));

import { useDemoStore } from '../../stores/demoStore';
import { useTaskStore } from '../../stores/taskStore';
import { TaskList } from './TaskList';

describe('B-1697 : en démo, la liste ne touche pas la vraie tâche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listTasks.mockResolvedValue([]);
    api.completeTask.mockResolvedValue({});
    useTaskStore.setState({
      tasks: [{
        id: 't1', title: 'Relancer Ruiz', description: null, status: 'todo', priority: 'medium', due_date: null,
        project_id: null, contact_id: null, tags: [], created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
      } as never],
      searchQuery: '', currentTaskId: null, isTaskFormOpen: false,
    });
    useDemoStore.setState({ enabled: true } as never);
  });
  afterEach(() => useDemoStore.setState({ enabled: false } as never));

  it('cocher « terminée » ne part pas', () => {
    render(<TaskList />);
    fireEvent.click(screen.getByRole('button', { name: 'Marquer la tâche Relancer Ruiz terminée' }));
    expect(api.completeTask).not.toHaveBeenCalled();
  });

  it('supprimer n’ouvre pas la confirmation', () => {
    render(<TaskList />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' }));
    expect(screen.queryByText(/Supprimer « Relancer Ruiz » \?/)).toBeNull();
  });
});
