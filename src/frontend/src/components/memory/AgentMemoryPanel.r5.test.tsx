import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { AgentMemoryPanel } from './AgentMemoryPanel';
import * as api from '../../services/api/crm-extended';
import { useDemoStore } from '../../stores/demoStore';

vi.mock('../../services/api/memoryCards', () => ({
  getMemoryCards: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  getMemoryScopes: vi.fn().mockResolvedValue([]), getMemoryCard: vi.fn(),
  patchMemoryCard: vi.fn(), deleteMemoryCard: vi.fn(), releaseMemoryCard: vi.fn(),
  listenMemoryChanges: () => () => {}, notifyMemoryChange: vi.fn(),
}));
vi.mock('../../services/api/crm-extended', () => ({ listActivities: vi.fn(), correctActivity: vi.fn(), deleteActivity: vi.fn() }));
const trace = { id: 'trace', type: 'agent_action', title: 'Action confirmée', description: null,
  contact_id: null, project_id: null, created_at: '2026-10-21T10:00:00Z',
  extra_data: '{"outcome":"indeterminee"}', statut: 'en_vigueur' } as api.ActivityResponse;
beforeEach(() => {
  vi.clearAllMocks(); useDemoStore.setState({ enabled: false });
  vi.mocked(api.listActivities).mockResolvedValue([trace]);
  vi.mocked(api.correctActivity).mockResolvedValue({ ...trace, id: 'correction' });
});
it('ouvre le journal, distingue une issue indéterminée et corrige par remplacement', async () => {
  render(<AgentMemoryPanel />);
  fireEvent.click(screen.getByRole('button', { name: /^Journal des actions/ }));
  expect(await screen.findByText('Issue indéterminée')).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Corriger cette trace' }));
  fireEvent.change(screen.getByLabelText('Ta correction'), { target: { value: 'Correction professionnelle' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enregistrer la correction' }));
  await waitFor(() => expect(api.correctActivity).toHaveBeenCalledWith('trace', 'Correction professionnelle'));
});
it('confirme l’effacement, reprend le focus après Échap et masque les traces en démo', async () => {
  render(<AgentMemoryPanel />);
  fireEvent.click(screen.getByRole('button', { name: /^Journal des actions/ }));
  const effacer = await screen.findByRole('button', { name: 'Effacer cette trace' });
  effacer.focus(); fireEvent.click(effacer);
  expect(screen.getByRole('alertdialog')).toBeVisible();
  fireEvent.keyDown(screen.getByRole('alertdialog'), { key: 'Escape' });
  await waitFor(() => expect(effacer).toHaveFocus());
  expect(api.deleteActivity).not.toHaveBeenCalled();
  useDemoStore.setState({ enabled: true });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Effacer cette trace' })).toBeDisabled());
  expect(screen.queryByText('Action confirmée')).not.toBeInTheDocument();
});
