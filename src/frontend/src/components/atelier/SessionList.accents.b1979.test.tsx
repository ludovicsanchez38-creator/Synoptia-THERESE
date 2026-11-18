/**
 * B-1979 : les commandes de la liste de sessions s'écrivent avec les accents,
 * comme « Relancer cette tâche ».
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useOpenClawStore } from '../../stores/openclawStore';
import { SessionList } from './SessionList';

describe('B-1979 : libellés accentués de la liste de sessions', () => {
  beforeEach(() => {
    useOpenClawStore.setState({
      sessions: [],
      sessionsLoading: false,
      error: null,
      openclawConnected: true,
      runningCount: 0,
      maxAgents: 3,
      fetchSessions: vi.fn().mockResolvedValue(undefined),
    } as never);
  });

  it('rafraîchir, nouvelle tâche et lancer une tâche portent les accents', () => {
    render(<SessionList />);
    expect(screen.getByRole('button', { name: 'Rafraîchir les sessions' })).toHaveAttribute('title', 'Rafraîchir');
    expect(screen.getByRole('button', { name: 'Lancer une nouvelle tâche' })).toHaveAttribute('title', 'Nouvelle tâche');
    expect(screen.getByRole('button', { name: 'Lancer une tâche' })).toBeInTheDocument();
  });
});
