/**
 * B-1407 (vérifié en corrigeant B-1398, cycle 13) : le conteneur déplaçable d'une
 * carte de tâche était un bouton sans nom. Comme les cartes du Pipeline
 * (B-877) et des projets (B-1398), il porte le titre de la tâche.
 */
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Task } from '../../services/api';
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

describe('B-1407 : la carte de tâche a un nom', () => {
  beforeEach(() => {
    useTaskStore.setState({ tasks: [TACHE], searchQuery: '', currentTaskId: null, isTaskFormOpen: false });
  });

  it('le conteneur déplaçable porte le titre de la tâche', () => {
    render(<TaskKanban />);
    const carte = document.querySelector('[aria-roledescription]') as HTMLElement;
    expect(carte.getAttribute('aria-label')).toBe('Relancer Sophie Moreau');
  });
});
