/**
 * Cycle 6, lecteur #189 (TaskForm.tsx) : l'effet de chargement dépendait de
 * l'objet `task` recalculé par `tasks.find` ; un rafraîchissement de la liste
 * pendant la saisie réécrivait les six champs avec les valeurs du serveur.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
}));

import { useTaskStore } from '../../stores/taskStore';
import { TaskForm } from './TaskForm';

const t1 = () => ({
  id: 't1', title: 'Relancer Ruiz', description: null, status: 'todo', priority: 'medium', due_date: null,
  project_id: null, contact_id: null, tags: [], created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
}) as never;

describe('#189 : un rafraîchissement de la liste n’efface pas la saisie en cours', () => {
  beforeEach(() => {
    useTaskStore.setState({ tasks: [t1()], currentTaskId: 't1', isTaskFormOpen: true, searchQuery: '' });
  });

  it('le titre modifié survit à une nouvelle instance de la même tâche', () => {
    render(<TaskForm />);
    const titre = screen.getByLabelText(/Titre/) as HTMLInputElement;
    expect(titre.value).toBe('Relancer Ruiz');
    fireEvent.change(titre, { target: { value: 'Relancer Ruiz demain matin' } });
    act(() => { useTaskStore.setState({ tasks: [t1()] }); });
    expect(titre.value).toBe('Relancer Ruiz demain matin');
  });
});
