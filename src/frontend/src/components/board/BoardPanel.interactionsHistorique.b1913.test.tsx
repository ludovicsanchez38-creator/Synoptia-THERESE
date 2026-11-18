import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listBoardDecisions: vi.fn().mockResolvedValue([{ id: 'd1', question: 'Quelle décision prendre ?', confidence: 'high', created_at: '2026-09-01T10:00:00Z' }]),
  getBoardDecision: vi.fn().mockResolvedValue({ id: 'd1', question: 'Quelle décision prendre ?', opinions: [], synthesis: { consensus_points: [], divergence_points: [], recommendation: 'Oui', confidence: 'high', next_steps: [] }, created_at: '2026-09-01T10:00:00Z' }),
  deleteBoardDecision: vi.fn(),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, base_url: '', models: [], error: null }),
}));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  ...api,
}));
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

it('B-1913 : la décision et ses commandes de suppression sont des interactions distinctes', async () => {
  render(<BoardPanel isOpen onClose={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
  const ouvrir = await screen.findByRole('button', { name: 'Quelle décision prendre ?' });
  const supprimer = screen.getByTitle('Supprimer');
  expect(ouvrir).not.toContainElement(supprimer);

  fireEvent.click(supprimer);
  const conserver = screen.getByRole('button', { name: 'Conserver la décision' });
  const confirmer = screen.getByRole('button', { name: 'Supprimer définitivement' });
  expect(ouvrir).not.toContainElement(conserver);
  expect(ouvrir).not.toContainElement(confirmer);
  expect(api.getBoardDecision).not.toHaveBeenCalled();
  fireEvent.click(conserver);
  fireEvent.keyDown(ouvrir, { key: 'Enter' });
  await waitFor(() => expect(api.getBoardDecision).toHaveBeenCalledWith('d1'));
});
