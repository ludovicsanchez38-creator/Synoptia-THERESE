/**
 * B-876 (cycle 9, relecteur U2) : les cartes de l'Historique étaient des
 * `<div onClick>` sans rôle ni tabIndex : impossible d'ouvrir une décision au
 * clavier, alors que le bouton Supprimer imbriqué, lui, prenait le focus.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn(),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, base_url: '', models: [], error: null }),
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

describe('BoardPanel - B-876, une décision de l’Historique s’ouvre au clavier', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockResolvedValue([{ id: 'd1', question: 'Passer ma société en SASU ?', recommendation: 'Oui', confidence: 'high', created_at: '2026-09-01T10:00:00Z' }]);
    apiMocks.getBoardDecision.mockResolvedValue({ id: 'd1', question: 'Passer ma société en SASU ?', opinions: [], synthesis: { recommendation: 'Oui', confidence: 'high', reasoning: '', risks: [], next_steps: [] }, created_at: '2026-09-01T10:00:00Z' });
  });

  it('la carte est un bouton nommé par sa question, Entrée l’ouvre', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
    const carte = await screen.findByRole('button', { name: /Passer ma société en SASU/ });
    expect(carte).toHaveAttribute('tabindex', '0');
    fireEvent.keyDown(carte, { key: 'Enter' });
    await waitFor(() => expect(apiMocks.getBoardDecision).toHaveBeenCalledWith('d1'));
  });
});
