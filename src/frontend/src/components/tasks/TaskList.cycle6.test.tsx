/**
 * Cycle 6, lecteur D105 (TaskList.tsx) : la carte de tâche était une
 * `motion.div` cliquable sans rôle ni clavier ; Tab atteignait cocher et
 * corbeille, jamais l'ouverture de la tâche.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockListTasks = vi.fn();
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => mockListTasks(...a),
}));

import { useTaskStore } from '../../stores/taskStore';
import { TaskList } from './TaskList';

describe('D105 : ouvrir une tâche se fait au clavier', () => {
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

  it('un bouton nommé d’après la tâche ouvre son formulaire', () => {
    render(<TaskList />);
    const ouvrir = screen.getByRole('button', { name: /Ouvrir la tâche Relancer Ruiz/ });
    fireEvent.click(ouvrir);
    expect(useTaskStore.getState().currentTaskId).toBe('t1');
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });
});
