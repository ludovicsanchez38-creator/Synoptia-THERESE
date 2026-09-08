/**
 * B-643 (persona Nadia, c4) : une action annulée affichait « Annulé » avec
 * une barre pleine à 100 %, l'étape 1 cochée et les étapes 2 et 3 en attente.
 * Sur une tâche annulée, la progression reflète les étapes réellement
 * terminées.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/actions', () => ({
  listAgents: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  listTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(),
  cancelTask: vi.fn(),
}));

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

const etape = (id: string, status: 'completed' | 'pending') => ({
  step_id: id, label: `Étape ${id}`, status, content: '', started_at: null, completed_at: null, error: null,
});

const tacheAnnulee = {
  task_id: 't-9',
  agent_id: 'relance-clients',
  agent_name: 'Relance clients',
  status: 'cancelled' as const,
  params: {},
  steps: [etape('1', 'completed'), etape('2', 'pending'), etape('3', 'pending')],
  result: '',
  created_at: '2026-09-08T00:00:00Z',
  started_at: '2026-09-08T00:00:00Z',
  completed_at: '2026-09-08T00:01:37Z',
  error: null,
  progress: 1,
};

describe('B-643 : une tâche annulée ne prétend pas être finie', () => {
  beforeEach(() => {
    useActionsStore.setState({ isPanelOpen: true, activeTask: tacheAnnulee as never, tasks: [tacheAnnulee] as never, selectedAgent: null } as never);
  });

  it('affiche la part des étapes terminées, pas 100 %', () => {
    render(<ActionPanel />);
    expect(screen.getByText('Annulé')).toBeInTheDocument();
    expect(screen.getByText('33%')).toBeInTheDocument();
    expect(screen.queryByText('100%')).toBeNull();
  });
});
