/**
 * B-1432 (recette P-146, lot 1, KO-1) : le menu « Filtrer par étiquette » ne
 * proposait pas le tag d'une tâche qu'on venait de créer : la liste des tags
 * n'était calculée qu'au chargement. Il fallait rafraîchir ou rouvrir l'écran.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useTaskStore } from '../../stores/taskStore';
import { TasksPanel } from './TasksPanel';

const { TACHE } = vi.hoisted(() => ({ TACHE: {
  id: 't-1', title: 'Envoyer le devis', description: null, status: 'todo', priority: 'medium',
  due_date: null, project_id: null, contact_id: null, tags: ['devis'],
  created_at: '2026-09-25T10:00:00', updated_at: '2026-09-25T10:00:00', completed_at: null,
} }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, listTasks: vi.fn().mockResolvedValue([TACHE]), listProjects: vi.fn().mockResolvedValue([]) };
});

function optionsDuMenu(): string[] {
  const menu = screen.getByRole('combobox', { name: 'Filtrer par étiquette' });
  return Array.from(menu.querySelectorAll('option')).map((o) => o.textContent ?? '');
}

describe('B-1432 : le menu des tags suit les tâches affichées', () => {
  it('propose le tag d’une tâche créée dans l’écran', async () => {
    useTaskStore.setState({ tasks: [], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
    render(<TasksPanel standalone />);
    await screen.findByText('Envoyer le devis');
    fireEvent.click(screen.getByRole('button', { name: 'Filtrer les tâches' }));
    expect(optionsDuMenu()).toContain('devis');
    act(() => {
      useTaskStore.getState().addTask({ ...TACHE, id: 't-2', title: 'Commander les plans', tags: ['atelier'] } as never);
    });
    expect(optionsDuMenu()).toContain('atelier');
  });
});
