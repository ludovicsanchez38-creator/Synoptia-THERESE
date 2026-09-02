/**
 * B-209 - terminer une tâche sans souris.
 *
 * En vue Kanban, « Marquer en cours » et « Marquer terminé » n'entraient dans
 * le DOM que sur `onMouseEnter` de la carte. Le focus clavier ne les faisait
 * pas apparaître : elles n'existaient que pour la souris, et la seule voie
 * restante au clavier était d'ouvrir la tâche puis son formulaire. Une
 * commande qu'aucun clavier n'atteint n'est pas une commande.
 *
 * Le focus atterrit sur le conteneur `useSortable` (celui qui porte
 * `tabIndex=0` et les écouteurs de dnd-kit), pas sur la carte : c'est là que
 * la révélation doit être branchée, sinon rien ne se déclenche.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TaskKanban } from './TaskKanban';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, updateTask: vi.fn().mockResolvedValue({}) };
});

const TACHE: Task = {
  id: 'tache-1',
  title: 'Relancer Sophie Moreau',
  description: null,
  status: 'todo',
  priority: 'medium',
  due_date: null,
  project_id: null,
  contact_id: null,
  tags: [],
  created_at: '2026-09-01T08:00:00Z',
  updated_at: '2026-09-01T08:00:00Z',
} as unknown as Task;

function carte(): HTMLElement {
  // Le conteneur focalisable posé par useSortable, au-dessus de la carte.
  const item = screen.getByTestId('task-item');
  const conteneur = item.parentElement;
  if (!conteneur) throw new Error('conteneur sortable introuvable');
  return conteneur;
}

describe('B-209 - les commandes de la carte Kanban existent aussi au clavier', () => {
  beforeEach(() => {
    useTaskStore.setState({
      tasks: [TACHE],
      searchQuery: '',
      currentTaskId: null,
      isTaskFormOpen: false,
    });
  });

  it('le focus sur la carte révèle « Marquer terminé »', () => {
    render(<TaskKanban />);

    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).toBeNull();
    fireEvent.focus(carte());
    expect(screen.getByRole('button', { name: 'Marquer terminé' })).toBeInTheDocument();
  });

  it('l’activer termine la tâche, sans ouvrir son formulaire', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());

    fireEvent.click(screen.getByRole('button', { name: 'Marquer terminé' }));

    // La commande part vraiment ; et le clic ne traverse pas jusqu'à la
    // carte, qui ouvrirait le formulaire à la place.
    expect(api.updateTask).toHaveBeenCalledWith(TACHE.id, { status: 'done' });
    expect(useTaskStore.getState().isTaskFormOpen).toBe(false);
  });

  it('quitter la carte au clavier referme les commandes', () => {
    render(<TaskKanban />);
    fireEvent.focus(carte());
    expect(screen.getByRole('button', { name: 'Marquer terminé' })).toBeInTheDocument();

    // `relatedTarget` hors de la carte : le focus part vraiment ailleurs.
    fireEvent.blur(carte(), { relatedTarget: document.body });
    expect(screen.queryByRole('button', { name: 'Marquer terminé' })).toBeNull();
  });
});
