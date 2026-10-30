/**
 * Tour 9 (relecture 8) : l'écran Mémoire montre quelles fiches attendent une
 * confirmation d'origine et permet d'attester « cette fiche vient de moi ».
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
const base = { kind: 'preference', content: 'Je préfère des devis courts', reason: '', subject: 'devis', version: 1,
  protected: false, author: 'therese', last_author: 'therese', scope: 'global', scope_name: 'Général', state: 'active',
  created_at: '2026-10-21T06:00:00Z', updated_at: '2026-10-21T06:01:00Z' };
const ancienne = { ...base, id: 'a', title: 'Devis courts', provenance_documents: 'inconnue' } as api.MemoryCard;
const documentaire = { ...base, id: 'd', title: 'Devis Maison Ambre', provenance_documents: 'documents' } as api.MemoryCard;
beforeEach(() => {
  vi.clearAllMocks();
  useDemoStore.setState({ enabled: false });
  useAgentMemoryStore.setState({ selectedId: null, sourceMessageId: null });
  vi.mocked(api.getMemoryCards).mockResolvedValue({ items: [ancienne, documentaire], total: 2 });
  vi.mocked(api.getMemoryScopes).mockResolvedValue([]);
  vi.mocked(api.patchMemoryCard).mockResolvedValue({ ...ancienne, version: 2, provenance_documents: 'sans_document' });
});

it('montre l’origine de chaque fiche et filtre celles à confirmer', async () => {
  render(<AgentMemoryPanel />);
  const meta = (fin: string) => (_: string, el: Element | null) => el?.tagName === 'P' && (el.textContent ?? '').endsWith(fin);
  expect(await screen.findByText(meta('· Origine à confirmer'))).toBeVisible();
  expect(screen.getByText(meta('· Issue d’un document'))).toBeVisible();
  fireEvent.change(screen.getByLabelText('Origine'), { target: { value: 'inconnue' } });
  await waitFor(() => expect(api.getMemoryCards).toHaveBeenLastCalledWith(expect.objectContaining({ provenance: 'inconnue' })));
});

it('atteste une ancienne fiche depuis son détail', async () => {
  vi.mocked(api.getMemoryCard).mockResolvedValue(ancienne);
  render(<AgentMemoryPanel />);
  fireEvent.click(await screen.findByRole('button', { name: 'Devis courts' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Cette fiche vient de moi' }));
  await waitFor(() => expect(api.patchMemoryCard).toHaveBeenCalledWith('a', { version: 1, atteste_par_utilisateur: true }));
});

it('ne propose pas l’attestation pour une fiche issue d’un document', async () => {
  vi.mocked(api.getMemoryCard).mockResolvedValue(documentaire);
  render(<AgentMemoryPanel />);
  fireEvent.click(await screen.findByRole('button', { name: 'Devis Maison Ambre' }));
  expect(await screen.findByText(/Réécris son titre et son contenu/)).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Cette fiche vient de moi' })).toBeNull();
});
