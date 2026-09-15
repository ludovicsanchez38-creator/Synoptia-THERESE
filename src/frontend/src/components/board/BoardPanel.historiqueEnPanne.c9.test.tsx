/**
 * B-873 (cycle 9, relecteur U4) : un échec de chargement de l'Historique
 * s'affichait « Aucune décision enregistrée » : une panne passait pour un
 * carnet vide, sans moyen de réessayer.
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

describe('BoardPanel - B-873, une panne de l’Historique n’est pas un carnet vide', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockRejectedValueOnce(new Error('HTTP 500')).mockResolvedValue([]);
  });

  it('dit que le chargement a échoué, propose de réessayer, puis montre le vrai état', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));

    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent(/Impossible de charger l’historique/);
    expect(screen.queryByText('Aucune décision enregistrée')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(await screen.findByText('Aucune décision enregistrée')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
