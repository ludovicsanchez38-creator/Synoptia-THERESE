/**
 * Tour 10 (relecture 9, réserve 2) : l'écran Mémoire compte les fiches
 * anciennes à confirmer et permet de les afficher d'un geste.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { AgentMemoryPanel } from './AgentMemoryPanel';
import * as api from '../../services/api/memoryCards';
import { useDemoStore } from '../../stores/demoStore';
import { useAgentMemoryStore } from '../../stores/agentMemoryStore';

vi.mock('../../services/api/memoryCards', () => ({
  getMemoryCards: vi.fn(), getMemoryCard: vi.fn(), getMemoryScopes: vi.fn(),
  patchMemoryCard: vi.fn(), deleteMemoryCard: vi.fn(), releaseMemoryCard: vi.fn(),
  notifyMemoryChange: vi.fn(), listenMemoryChanges: () => () => {},
}));
const ancienne = { id: 'a', kind: 'preference', title: 'Vouvoiement', content: 'Je préfère que tu me vouvoies', reason: '',
  subject: 'ton', version: 1, protected: false, author: 'therese', last_author: 'therese', scope: 'global',
  scope_name: 'Général', state: 'active', created_at: '2026-10-21T06:00:00Z', updated_at: '2026-10-21T06:01:00Z',
  provenance_documents: 'inconnue' } as api.MemoryCard;
beforeEach(() => {
  vi.clearAllMocks();
  useDemoStore.setState({ enabled: false });
  useAgentMemoryStore.setState({ selectedId: null, sourceMessageId: null });
  vi.mocked(api.getMemoryScopes).mockResolvedValue([]);
});

it('compte les fiches à confirmer et les affiche d’un geste', async () => {
  vi.mocked(api.getMemoryCards).mockImplementation(async (params = {}) =>
    params.provenance === 'inconnue' ? { items: [ancienne], total: 3 } : { items: [], total: 0 });
  render(<AgentMemoryPanel />);
  const bandeau = await screen.findByRole('status', { name: /fiches à confirmer/ });
  expect(bandeau).toHaveTextContent('3 fiches anciennes attendent ta confirmation');
  fireEvent.click(screen.getByRole('button', { name: 'Les afficher' }));
  await waitFor(() => expect(screen.getByLabelText('Origine')).toHaveValue('inconnue'));
});

it('n’affiche aucun bandeau sans fiche à confirmer', async () => {
  vi.mocked(api.getMemoryCards).mockResolvedValue({ items: [], total: 0 });
  render(<AgentMemoryPanel />);
  await screen.findByText(/Rien de noté pour le moment/);
  expect(screen.queryByRole('status', { name: /fiches à confirmer/ })).toBeNull();
});
