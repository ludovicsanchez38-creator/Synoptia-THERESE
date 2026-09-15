/**
 * B-872 (cycle 9, relecteur U4) : supprimer une décision de l'Historique
 * passait par `confirm()` natif, non garanti sous Tauri et hors charte
 * (règle D62/D106 : confirmation en ligne, fail-closed).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn(),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn().mockResolvedValue(undefined),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, base_url: '', models: [], error: null }),
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

const decision = { id: 'd1', question: 'Passer ma société en SASU ?', recommendation: 'Oui', confidence: 'high', created_at: '2026-09-01T10:00:00Z' };

describe('BoardPanel - B-872, la suppression d’une décision se confirme en ligne', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockResolvedValue([decision]);
    vi.stubGlobal('confirm', vi.fn(() => { throw new Error('confirm() natif interdit'); }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('ne supprime rien au premier clic, puis supprime sur « Supprimer définitivement »', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
    await screen.findByText('Passer ma société en SASU ?');

    fireEvent.click(screen.getByTitle('Supprimer'));
    expect(apiMocks.deleteBoardDecision).not.toHaveBeenCalled();
    expect(screen.getByText(/Supprimer cette décision/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Conserver la décision' }));
    expect(screen.queryByText(/Supprimer cette décision/)).toBeNull();

    fireEvent.click(screen.getByTitle('Supprimer'));
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));
    await waitFor(() => expect(apiMocks.deleteBoardDecision).toHaveBeenCalledWith('d1'));
    expect(screen.queryByText('Passer ma société en SASU ?')).toBeNull();
  });
});
