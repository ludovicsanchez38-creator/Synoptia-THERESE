/**
 * Cycle 6, lecteur D106 (TaskList.tsx) : la corbeille passait par le
 * `confirm()` natif, comme le détail d'un rendez-vous (D62) : boîte non
 * garantie sous Tauri, hors charte, non stylable. Confirmation en ligne.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), deleteTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => api.listTasks(...a),
  deleteTask: (...a: unknown[]) => api.deleteTask(...a),
}));

import { useTaskStore } from '../../stores/taskStore';
import { TaskList } from './TaskList';

describe('D106 : supprimer une tâche se confirme dans l’application', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listTasks.mockResolvedValue([]);
    api.deleteTask.mockResolvedValue(undefined);
    useTaskStore.setState({
      tasks: [{
        id: 't1', title: 'Relancer Ruiz', description: null, status: 'todo', priority: 'medium', due_date: null,
        project_id: null, contact_id: null, tags: [], created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
      } as never],
      searchQuery: '', currentTaskId: null, isTaskFormOpen: false,
    });
  });

  it('le premier clic ne supprime rien et annonce la tâche par son titre', () => {
    render(<TaskList />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' }));
    expect(api.deleteTask).not.toHaveBeenCalled();
    expect(screen.getByText(/Supprimer « Relancer Ruiz » \?/)).toBeInTheDocument();
  });

  it('on peut renoncer ; confirmer appelle l’API une fois', async () => {
    render(<TaskList />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' }));
    fireEvent.click(screen.getByRole('button', { name: 'Conserver la tâche' }));
    expect(screen.queryByText(/Supprimer « Relancer Ruiz » \?/)).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer la tâche Relancer Ruiz' }));
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));
    await waitFor(() => expect(api.deleteTask).toHaveBeenCalledWith('t1'));
    await waitFor(() => expect(useTaskStore.getState().tasks).toHaveLength(0));
  });
});
