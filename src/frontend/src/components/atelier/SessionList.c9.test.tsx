/**
 * B-779 (cycle 9) : « Relancer cette tâche » restait cliquable pendant l'envoi,
 * contrairement aux autres entrées vers dispatchTask ; un double clic relançait deux fois.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useOpenClawStore } from '../../stores/openclawStore';
import { SessionList } from './SessionList';

describe('SessionList - B-779, Relancer est neutralisé pendant l’envoi', () => {
  let resoudre!: (v: unknown) => void;
  const dispatchTask = vi.fn(() => new Promise((r) => { resoudre = r; }));
  beforeEach(() => {
    dispatchTask.mockClear();
    useOpenClawStore.setState({
      sessions: [{ id: 's1', status: 'error', instruction: 'Veille concurrents', created_at: new Date().toISOString() } as never],
      sessionsLoading: false, error: null, openclawConnected: true, runningCount: 0, maxAgents: 3,
      fetchSessions: vi.fn().mockResolvedValue(undefined), dispatchTask,
    } as never);
  });

  it('désactive le bouton le temps de dispatchTask et n’envoie qu’une fois', async () => {
    render(<SessionList />);
    const relancer = screen.getByRole('button', { name: /Relancer cette t/ });
    fireEvent.click(relancer);
    fireEvent.click(relancer);
    expect(dispatchTask).toHaveBeenCalledTimes(1);
    expect(relancer).toBeDisabled();
    resoudre(null);
    await waitFor(() => expect(relancer).toBeEnabled());
  });
});
