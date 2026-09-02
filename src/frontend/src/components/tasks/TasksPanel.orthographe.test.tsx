/**
 * B-210 - le compteur de l'écran Tâches écrivait « tache » sans accent.
 *
 * Le défaut est fermé depuis le lot RE08 (commit 329e2aa8, sous B-221) : ce
 * fichier pose le VERROU qui manquait. L'écart était interne à un seul
 * en-tête - le libellé de vue disait « Tâches », le bouton « Nouvelle tâche »,
 * les colonnes « Aucune tâche », et la ligne du dessous « 0 tache ». Une faute
 * isolée au milieu d'un écran correct se relit sans se voir : c'est un test
 * qui doit la retenir, pas une relecture.
 *
 * La règle porte sur le compteur RENDU, singulier comme pluriel, et refuse la
 * forme sans accent partout dans l'en-tête.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Task } from '../../services/api';
import { useTaskStore } from '../../stores/taskStore';
import { TasksPanel } from './TasksPanel';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, listTasks: vi.fn().mockResolvedValue([]), listProjects: vi.fn().mockResolvedValue([]) };
});

function tache(id: string): Task {
  return {
    id,
    title: `Tâche ${id}`,
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
}

function poser(taches: Task[]) {
  useTaskStore.setState({
    tasks: taches,
    searchQuery: '',
    currentTaskId: null,
    isTaskFormOpen: false,
  });
}

describe('B-210 - le compteur des Tâches accentue « tâche »', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('zéro tâche : « 0 tâche », au singulier et accentué', () => {
    poser([]);
    render(<TasksPanel standalone />);

    expect(screen.getByText(/^0 tâche$/)).toBeInTheDocument();
  });

  it('deux tâches : « 2 tâches », au pluriel et accentué', () => {
    poser([tache('t1'), tache('t2')]);
    render(<TasksPanel standalone />);

    expect(screen.getByText(/^2 tâches$/)).toBeInTheDocument();
  });

  it('la forme sans accent n’apparaît nulle part dans l’écran', () => {
    poser([tache('t1')]);
    const { container } = render(<TasksPanel standalone />);

    // Le corps du texte rendu, attributs compris (title, aria-label).
    expect(container.innerHTML).not.toMatch(/\btaches?\b/i);
  });
});
