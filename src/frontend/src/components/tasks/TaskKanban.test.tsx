/**
 * Tests TaskKanban - régression du pattern « poignée seule » (jumeau BUG-041).
 *
 * Comme ProjectsKanban avant son fix, les listeners de useSortable n'étaient
 * posés que sur la poignée GripVertical (16px, quasi invisible) : attraper la
 * carte tâche par son corps - le geste naturel - ne démarrait aucun drag.
 * Ces tests vérifient que le drag s'active depuis le corps de la carte
 * (pointeur et clavier) et que le clic simple continue d'ouvrir la tâche.
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { TaskKanban } from './TaskKanban';
import { useTaskStore } from '../../stores/taskStore';
import type { Task } from '../../services/api';

function makeTask(overrides: Partial<Task> & Pick<Task, 'id' | 'title' | 'status'>): Task {
  return {
    description: null,
    priority: 'medium',
    due_date: null,
    tags: null,
    contact_id: null,
    project_id: null,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  } as Task;
}

const tasks: Task[] = [
  makeTask({ id: 't-alpha', title: 'Tâche Alpha', status: 'todo' }),
  makeTask({ id: 't-gamma', title: 'Tâche Gamma', status: 'in_progress' }),
];

function renderKanban() {
  useTaskStore.setState({
    tasks,
    searchQuery: '',
    currentTaskId: null,
    isTaskFormOpen: false,
  });
  render(<TaskKanban />);
}

/** Le wrapper sortable de la carte (élément portant role + tabIndex posés par useSortable). */
function getSortableWrapper(taskTitle: string): HTMLElement {
  const title = screen.getByText(taskTitle);
  const wrapper = title.closest('[aria-roledescription="sortable"]');
  if (!(wrapper instanceof HTMLElement)) {
    throw new Error(`Wrapper sortable introuvable pour ${taskTitle}`);
  }
  return wrapper;
}

describe('TaskKanban drag & drop (jumeau BUG-041)', () => {
  beforeEach(() => {
    useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: false });
  });

  // NB : ce test passe AVANT les tests de drag - après un drag, dnd-kit arme
  // une suppression du prochain click (anti-clic parasite post-drop) qui
  // avalerait le clic de ce test.
  it('un clic simple sur le titre ouvre toujours la tâche (pas de drag parasite)', () => {
    renderKanban();

    fireEvent.click(screen.getByText('Tâche Alpha'));

    expect(useTaskStore.getState().currentTaskId).toBe('t-alpha');
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });

  it('démarre un drag au pointeur depuis le corps de la carte (pas seulement la poignée)', () => {
    renderKanban();

    // Geste utilisateur : attraper la carte par son titre, puis bouger au-delà
    // de l'activationConstraint (distance 8px).
    const title = screen.getByText('Tâche Alpha');
    fireEvent.pointerDown(title, {
      button: 0,
      isPrimary: true,
      pointerId: 1,
      clientX: 5,
      clientY: 5,
    });
    fireEvent.pointerMove(document, { pointerId: 1, clientX: 5, clientY: 40 });

    // Drag actif = le DragOverlay rend une seconde carte de la même tâche.
    expect(screen.getAllByText('Tâche Alpha')).toHaveLength(2);

    fireEvent.pointerUp(document, { pointerId: 1 });
    // Consomme la suppression de click armée par dnd-kit après le drag,
    // pour ne pas polluer un éventuel test suivant.
    fireEvent.click(document);
  });

  it('démarre un drag au clavier depuis la carte focusée (Entrée)', async () => {
    renderKanban();

    const wrapper = getSortableWrapper('Tâche Gamma');
    wrapper.focus();
    fireEvent.keyDown(wrapper, { code: 'Enter' });

    expect(screen.getAllByText('Tâche Gamma')).toHaveLength(2);

    // Terminer proprement le drag, sinon son état pollue le test suivant.
    // Le KeyboardSensor attache son listener keydown au document dans un
    // setTimeout(0) : il faut laisser passer un tick avant d'annuler.
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.keyDown(wrapper, { code: 'Escape' });
    await waitFor(() => expect(screen.getAllByText('Tâche Gamma')).toHaveLength(1));
  });
});
