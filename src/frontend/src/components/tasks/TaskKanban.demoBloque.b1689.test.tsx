/**
 * B-1689 (suite de B-1621, décision de Ludo du 26/09) : en démo, déplacer une
 * tâche de colonne (glisser ou « Marquer terminé ») écrivait sur la vraie
 * tâche. Le glisser et le bouton passent par le même changement de statut.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import type { Task } from '../../services/api';
import { useDemoStore } from '../../stores/demoStore';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, updateTask: vi.fn().mockResolvedValue({}) };
});

const TACHE = {
  id: 'tache-1', title: 'Relancer Sophie Moreau', description: null, status: 'todo', priority: 'medium',
  due_date: null, project_id: null, contact_id: null, tags: [],
  created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

describe('B-1689 : en démo, le kanban ne déplace pas la vraie tâche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useTaskStore.setState({ tasks: [TACHE], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    useDemoStore.setState({ enabled: true } as never);
  });
  afterEach(() => useDemoStore.setState({ enabled: false } as never));

  it('« Marquer terminé » ne part pas', () => {
    render(<TaskKanban />);
    fireEvent.focus(screen.getByTestId('task-item').parentElement as HTMLElement);
    fireEvent.click(screen.getByRole('button', { name: 'Marquer terminé' }));
    expect(api.updateTask).not.toHaveBeenCalled();
  });
});
