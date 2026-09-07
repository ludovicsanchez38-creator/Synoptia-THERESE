/** B-616 (Karim, c4) : le filtre de statut écrivait « A faire » sans accent, face à la colonne « À faire ». */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useTaskStore } from '../../stores/taskStore';
import { TasksPanel } from './TasksPanel';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, listTasks: vi.fn().mockResolvedValue([]), listProjects: vi.fn().mockResolvedValue([]) };
});

describe('TasksPanel : les statuts portent leurs accents', () => {
  it('le filtre propose « À faire »', async () => {
    useTaskStore.setState({ tasks: [], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TasksPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: 'Filtrer les tâches' }));
    const options = Array.from(document.querySelectorAll('option')).map((o) => o.textContent);
    expect(options).toContain('À faire');
    expect(options).not.toContain('A faire');
  });
});
