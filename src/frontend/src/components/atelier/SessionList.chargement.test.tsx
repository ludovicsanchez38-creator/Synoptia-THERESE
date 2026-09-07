/**
 * B-401 (cycle 4) : l'état vide « Aucune session » s'affichait pendant le
 * chargement, ce qui annonçait à un lecteur d'écran une absence avant même
 * que la réponse ne soit arrivée (même famille que B-527 et B-537).
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useOpenClawStore } from '../../stores/openclawStore';
import { SessionList } from './SessionList';

describe('SessionList : chargement avant état vide (B-401)', () => {
  beforeEach(() => {
    useOpenClawStore.setState({
      sessions: [],
      error: null,
      openclawConnected: true,
      runningCount: 0,
      maxAgents: 3,
      fetchSessions: vi.fn().mockResolvedValue(undefined),
    } as never);
  });

  it('pendant la lecture, dit « Lecture des sessions » et pas « Aucune session »', () => {
    useOpenClawStore.setState({ sessionsLoading: true } as never);
    render(<SessionList />);
    expect(screen.getByRole('status')).toHaveTextContent(/Lecture des sessions/);
    expect(screen.queryByText('Aucune session')).not.toBeInTheDocument();
  });

  it('une fois lue et vide, dit « Aucune session »', () => {
    useOpenClawStore.setState({ sessionsLoading: false } as never);
    render(<SessionList />);
    expect(screen.getByText('Aucune session')).toBeInTheDocument();
  });
});
