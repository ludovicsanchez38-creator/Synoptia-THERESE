/**
 * B-900 (cycle 9, relecteur V4) : ouvrir ou supprimer une décision de
 * l'Historique échouait en silence (console.error seul) alors que la liste,
 * elle, dit sa panne depuis B-873.
 */
import { fireEvent, render, screen } from '@testing-library/react';
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

describe('BoardPanel - B-900, ouvrir ou supprimer une décision dit son échec', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockResolvedValue([{ id: 'd1', question: 'Passer ma société en SASU ?', recommendation: 'Oui', confidence: 'high', created_at: '2026-09-01T10:00:00Z' }]);
    apiMocks.getBoardDecision.mockRejectedValue(new Error('HTTP 500'));
    apiMocks.deleteBoardDecision.mockRejectedValue(new Error('HTTP 500'));
  });

  it('une ouverture en échec affiche une alerte, la liste reste', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Passer ma société en SASU/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Impossible d’ouvrir cette décision/);
    expect(screen.getByText('Passer ma société en SASU ?')).toBeInTheDocument();
  });

  it('une suppression en échec affiche une alerte, la décision reste', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
    await screen.findByText('Passer ma société en SASU ?');
    fireEvent.click(screen.getByTitle('Supprimer'));
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Impossible de supprimer cette décision/);
    expect(screen.getByText('Passer ma société en SASU ?')).toBeInTheDocument();
  });
});
