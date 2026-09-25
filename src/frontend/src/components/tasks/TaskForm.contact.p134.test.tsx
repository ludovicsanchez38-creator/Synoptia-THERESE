/**
 * P-134 (persona Nathalie, cycle 13) : « Nouvelle tâche » n'avait pas de
 * champ contact ; une relance posée en tâche n'était reliée à personne. Le
 * moteur sait lier une tâche à une fiche (`Task.contact_id`), le formulaire
 * ne le proposait pas.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ createTask: vi.fn(), updateTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
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

describe('P-134 : une tâche reliée à une personne', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useContactsStore.setState({ contacts: [karim] as never, loaded: true, fetchContacts: vi.fn().mockResolvedValue(undefined) } as never);
    apiMocks.createTask.mockImplementation(async (r) => ({ id: 't1', ...r, status: 'todo', priority: 'medium', tags: null, completed_at: null, created_at: '', updated_at: '' }));
    apiMocks.updateTask.mockImplementation(async (id, r) => ({ id, ...r }));
  });

  it('à la création, le contact choisi part avec la tâche', async () => {
    useTaskStore.setState({ tasks: [], currentTaskId: null } as never);
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Karim Benali' } });
    fireEvent.change(screen.getByLabelText('Contact'), { target: { value: 'c-karim' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    await waitFor(() => expect(apiMocks.createTask).toHaveBeenCalledTimes(1));
    expect(apiMocks.createTask.mock.calls[0][0]).toMatchObject({ contact_id: 'c-karim' });
  });

  it('en modification, le contact lu s’affiche et peut se retirer', async () => {
    useTaskStore.setState({
      tasks: [{ id: 't1', title: 'Relancer Karim', description: null, status: 'todo', priority: 'medium', due_date: null, project_id: null, contact_id: 'c-karim', tags: null, completed_at: null, created_at: '', updated_at: '' }],
      currentTaskId: 't1',
    } as never);
    render(<TaskForm />);
    const champ = screen.getByLabelText('Contact') as HTMLSelectElement;
    await waitFor(() => expect(champ.value).toBe('c-karim'));
    fireEvent.change(champ, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    await waitFor(() => expect(apiMocks.updateTask).toHaveBeenCalledTimes(1));
    expect(apiMocks.updateTask.mock.calls[0][1]).toMatchObject({ contact_id: null });
  });
});
