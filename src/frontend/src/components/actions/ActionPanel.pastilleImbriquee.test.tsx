/**
 * B-362 (05/09/2026) : la pastille flottante était un bouton contenant un
 * second contrôle focalisable (annuler). Deux commandes, deux boutons frères.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/actions', () => ({
  listAgents: vi.fn().mockResolvedValue([]), runAction: vi.fn(), listTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(), cancelTask: vi.fn(),
}));

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

const tacheEnCours = {
  task_id: 't-1', agent_id: 'rapport-hebdo', agent_name: 'Rapport hebdo', status: 'running' as const,
  params: {}, steps: [], result: '', created_at: '2026-09-05T10:00:00Z',
  started_at: '2026-09-05T10:00:00Z', completed_at: null, error: null, progress: 0.4,
};

describe('ActionPanel : pastille sans contrôle imbriqué (B-362)', () => {
  beforeEach(() => {
    useActionsStore.setState({ isPanelOpen: false, activeTask: tacheEnCours as never, tasks: [tacheEnCours] as never });
  });

  it('ouvrir et annuler sont deux boutons natifs distincts, aucun dans l’autre', () => {
    render(<ActionPanel />);
    const ouvrir = screen.getByRole('button', { name: /Rapport hebdo en cours/i });
    const annuler = screen.getByRole('button', { name: /Annuler l.action/i });
    expect(ouvrir.tagName).toBe('BUTTON');
    expect(annuler.tagName).toBe('BUTTON');
    expect(ouvrir.contains(annuler)).toBe(false);
    expect(annuler.contains(ouvrir)).toBe(false);
    expect(ouvrir.querySelectorAll('button, [role="button"]')).toHaveLength(0);
  });
});
