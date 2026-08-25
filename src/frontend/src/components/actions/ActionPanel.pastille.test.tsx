/**
 * Revue jalon 0.47 (F10) : la pastille flottante (panneau fermé) doit dire
 * la vérité pour `cancel_requested` - « Arrêt en cours... », sans re-proposer
 * un bouton d'annulation pour une demande déjà retenue.
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

const tacheArretDemande = {
  task_id: 't-1',
  agent_id: 'rapport-hebdo',
  agent_name: 'Rapport hebdo',
  status: 'cancel_requested' as const,
  params: {},
  steps: [],
  result: '',
  created_at: '2026-08-25T10:00:00Z',
  started_at: '2026-08-25T10:00:00Z',
  completed_at: null,
  error: null,
  progress: 0.4,
};

describe('ActionPanel - pastille fermée', () => {
  beforeEach(() => {
    useActionsStore.setState({
      isPanelOpen: false,
      activeTask: tacheArretDemande as never,
      tasks: [tacheArretDemande] as never,
    });
  });

  it('affiche « Arrêt en cours » sans bouton d’annulation', () => {
    render(<ActionPanel />);

    expect(screen.getByText(/Arrêt en cours/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /annuler/i })).toBeNull();
  });
});
