/**
 * B-767 (cycle 9) : un échec de chargement du diff était avalé ; le panneau
 * annonçait « 0 ajouts, 0 suppressions, 0 fichier touché » et « Appliquer les
 * changements » restait actif. Sans diff, on le dit, et on n'applique rien.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  approveTask: vi.fn(), rejectTask: vi.fn(), getAgentTask: vi.fn(), getTaskDiff: vi.fn(),
}));

import { getTaskDiff } from '../../services/api/agents';
import { useAtelierStore } from '../../stores/atelierStore';
import { CodeReviewPanel } from './CodeReviewPanel';

describe('CodeReviewPanel - B-767, un diff non chargé ne se présente pas comme vide', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAtelierStore.setState({
      currentMission: { id: 'm-1', taskId: 'task-1', summary: 'Corriger le libellé', phase: 'review' } as never,
    } as never);
  });

  it('dit que les modifications n’ont pas pu être chargées et désactive Appliquer', async () => {
    vi.mocked(getTaskDiff).mockRejectedValue(new Error('HTTP 503'));
    render(<CodeReviewPanel />);

    await waitFor(() => expect(getTaskDiff).toHaveBeenCalledWith('task-1'));
    expect(await screen.findByRole('alert')).toHaveTextContent(/modifications n’ont pas pu être chargées/);
    expect(screen.queryByText(/0 fichier touché/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Appliquer les changements' })).toBeDisabled();
  });
});
