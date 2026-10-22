import { act, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { ActivityMemoryBranch } from './ActivityMemoryBranch';
import { listActivities } from '../../services/api/crm-extended';
vi.mock('../../services/api/crm-extended', () => ({ listActivities: vi.fn(), correctActivity: vi.fn(), deleteActivity: vi.fn() }));
it('retire immédiatement une trace périmée après effacement dans une autre vue, même si la relecture échoue', async () => {
  vi.mocked(listActivities).mockResolvedValueOnce([{ id: 'trace', type: 'agent_action', title: 'SENTINELLE_EFFACEE',
    contact_id: null, description: null, extra_data: '{}', created_at: '2026-10-21T10:00:00Z' }]).mockRejectedValue(new Error('Panne factice'));
  render(<ActivityMemoryBranch />);
  expect(await screen.findByText('SENTINELLE_EFFACEE')).toBeVisible();
  act(() => { window.dispatchEvent(new Event('therese:memory-cards-changed')); });
  await waitFor(() => expect(screen.queryByText('SENTINELLE_EFFACEE')).not.toBeInTheDocument());
  expect(await screen.findByRole('alert')).toHaveTextContent('Impossible');
});
