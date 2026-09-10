/**
 * Cycle 6, lecteur D195 (SessionList.tsx) : l'erreur de lecture n'était
 * rendue que si la liste était vide. Avec des sessions déjà affichées, un
 * rafraîchissement en panne restait muet et la liste passait pour à jour.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useOpenClawStore } from '../../stores/openclawStore';
import { SessionList } from './SessionList';

describe('D195 : une panne de rafraîchissement est dite même liste pleine', () => {
  beforeEach(() => {
    useOpenClawStore.setState({
      sessions: [{ id: 's1', status: 'running', instruction: 'Veille concurrents', created_at: new Date().toISOString() } as never],
      sessionsLoading: false,
      error: 'Erreur chargement sessions',
      openclawConnected: true,
      runningCount: 1,
      maxAgents: 3,
      fetchSessions: vi.fn().mockResolvedValue(undefined),
    } as never);
  });

  it('affiche une alerte au-dessus de la liste, sans cacher les sessions', () => {
    render(<SessionList />);
    expect(screen.getByRole('alert')).toHaveTextContent(/Erreur chargement sessions/);
    expect(screen.getByText('Veille concurrents')).toBeInTheDocument();
  });
});
