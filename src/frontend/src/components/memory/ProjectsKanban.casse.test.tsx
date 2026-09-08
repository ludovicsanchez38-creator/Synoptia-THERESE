/** P-046 (Karim, c4, accepté par Ludo le 08/09) : les en-têtes des deux kanbans (tâches « À faire », projets « ACTIF ») n'avaient pas la même casse. Une seule : la casse de phrase du lexique, celle du kanban des tâches. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ProjectsKanban } from './ProjectsKanban';
import { TaskKanban } from '../tasks/TaskKanban';
import { useTaskStore } from '../../stores/taskStore';
import type { Project } from '../../services/api';

const projet: Project = {
  id: 'p-1', name: 'Projet Alpha', status: 'active', description: null, contact_id: null, budget: null, notes: null, tags: null,
  created_at: '2026-06-01T00:00:00Z', updated_at: '2026-06-01T00:00:00Z',
};

describe('Casse des en-têtes de colonnes (P-046)', () => {
  it('le kanban des projets écrit ses colonnes en casse de phrase, comme celui des tâches', () => {
    render(<ProjectsKanban projects={[projet]} onSelect={vi.fn()} onDelete={vi.fn()} onStatusChange={vi.fn()} />);
    const enTeteProjets = screen.getByText('Actif');
    expect(enTeteProjets.className).not.toMatch(/\buppercase\b/);

    useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: false });
    render(<TaskKanban />);
    const enTeteTaches = screen.getByText('À faire');
    expect(enTeteTaches.className).not.toMatch(/\buppercase\b/);
  });
});
