/**
 * P-150 (recette P-146, lot 1 ; acceptée le 25/09) : le filtre projet des
 * Tâches existait, mais aucun écran ne posait le projet d'une tâche ; il
 * rendait toujours une liste vide. Le champ « Projet lié » du formulaire
 * était en commentaire.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ createTask: vi.fn(), updateTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([{ id: 'p-cuisine', name: 'Cuisine Roux' }]),
  listContacts: vi.fn().mockResolvedValue([]),
  createTask: apiMocks.createTask,
  updateTask: apiMocks.updateTask,
}));

import { TaskForm } from './TaskForm';
import { useTaskStore } from '../../stores/taskStore';
import { useContactsStore } from '../../stores/contactsStore';

const karim = {
  id: 'c-karim', first_name: 'Karim', last_name: 'Benali', company: null, email: null, phone: '06 00 00 00 00',
  address: null, notes: null, tags: [], stage: 'discovery', score: 60, source: null, last_interaction: null,
  created_at: '2026-09-20T09:00:00', updated_at: '2026-09-20T09:00:00',
};

describe('P-150 : une tâche rattachée à un projet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({ contacts: [karim] as never, loaded: true, fetchContacts: vi.fn().mockResolvedValue(undefined) } as never);
    apiMocks.createTask.mockImplementation(async (r) => ({ id: 't1', ...r, status: 'todo', priority: 'medium', tags: null, completed_at: null, created_at: '', updated_at: '' }));
    apiMocks.updateTask.mockImplementation(async (id, r) => ({ id, ...r }));
  });

  it('à la création, le projet choisi part avec la tâche', async () => {
    useTaskStore.setState({ tasks: [], currentTaskId: null } as never);
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Commander le plan de travail' } });
    const projet = screen.getByLabelText('Projet lié') as HTMLSelectElement;
    await waitFor(() => expect(Array.from(projet.options).map((o) => o.textContent)).toContain('Cuisine Roux'));
    fireEvent.change(projet, { target: { value: 'p-cuisine' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    await waitFor(() => expect(apiMocks.createTask).toHaveBeenCalledTimes(1));
    expect(apiMocks.createTask.mock.calls[0][0]).toMatchObject({ project_id: 'p-cuisine' });
  });

  it('en modification, le projet lu s’affiche et peut se retirer', async () => {
    useTaskStore.setState({
      tasks: [{ id: 't1', title: 'Commander', description: null, status: 'todo', priority: 'medium', due_date: null, project_id: 'p-cuisine', contact_id: null, tags: null, completed_at: null, created_at: '', updated_at: '' }],
      currentTaskId: 't1',
    } as never);
    render(<TaskForm />);
    const projet = screen.getByLabelText('Projet lié') as HTMLSelectElement;
    await waitFor(() => expect(projet.value).toBe('p-cuisine'));
    fireEvent.change(projet, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    await waitFor(() => expect(apiMocks.updateTask).toHaveBeenCalledTimes(1));
    expect(apiMocks.updateTask.mock.calls[0][1]).toMatchObject({ project_id: null });
  });
});
