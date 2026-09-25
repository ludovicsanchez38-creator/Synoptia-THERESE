/**
 * P-151 (recette P-146, lot 1 ; acceptée le 25/09) : le lien posé par P-134
 * (la personne d'une tâche) ne se voyait ni sur la ligne ni sur la carte.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockListTasks = vi.fn();
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listTasks: (...a: unknown[]) => mockListTasks(...a),
}));

import { useContactsStore } from '../../stores/contactsStore';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';
import { TaskList } from './TaskList';

const tache = {
  id: 't1', title: 'Relancer le devis', description: null, status: 'todo', priority: 'medium', due_date: null,
  project_id: null, contact_id: 'c1', tags: [], created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
};

describe('P-151 : la personne liée se voit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListTasks.mockResolvedValue([]);
    useTaskStore.setState({ tasks: [tache as never], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    useContactsStore.setState({
      contacts: [{ id: 'c1', first_name: 'Julien', last_name: 'Garnier', company: 'Garnier Bois', email: null } as never],
      loaded: true,
    });
  });

  it('sur la ligne de la liste', () => {
    render(<TaskList />);
    expect(screen.getByText('Julien Garnier')).toBeInTheDocument();
  });

  it('sur la carte du tableau', () => {
    render(<TaskKanban />);
    expect(screen.getByText('Julien Garnier')).toBeInTheDocument();
  });
});

describe('P-151 : le panneau Tâches charge le carnet pour nommer les personnes', () => {
  it('ouvert sans carnet chargé, il le charge', async () => {
    const { TasksPanel } = await import('./TasksPanel');
    const { waitFor } = await import('@testing-library/react');
    const charger = vi.fn().mockResolvedValue(undefined);
    useContactsStore.setState({ contacts: [], loaded: false, fetchContacts: charger } as never);
    render(<TasksPanel standalone />);
    await waitFor(() => expect(charger).toHaveBeenCalled());
  });
});
