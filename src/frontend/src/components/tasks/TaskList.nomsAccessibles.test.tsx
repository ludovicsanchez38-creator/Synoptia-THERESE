/** B-622 (Karim, c4) : les boutons « terminer » et « supprimer » de la liste n'avaient pas de nom accessible. */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockListTasks = vi.fn();
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => mockListTasks(...a),
}));

import { useTaskStore } from '../../stores/taskStore';
import { TaskList } from './TaskList';

describe('TaskList : chaque bouton a un nom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListTasks.mockResolvedValue([]);
    useTaskStore.setState({
      tasks: [{
        id: 't1', title: 'Relancer Ruiz', description: null, status: 'todo', priority: 'medium', due_date: null,
        project_id: null, contact_id: null, tags: [], created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
      } as never],
      searchQuery: '', currentTaskId: null, isTaskFormOpen: false,
    });
  });

  it('nomme le bouton de terminaison et celui de suppression', () => {
    render(<TaskList />);
    expect(screen.getByRole('button', { name: /Marquer .*terminée|Terminer/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Supprimer/i })).toBeInTheDocument();
  });
});
