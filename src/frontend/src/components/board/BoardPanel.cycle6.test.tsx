/**
 * Cycle 6, lecteur #110 (BoardPanel.tsx) : sur un événement SSE `error`,
 * `runError` était posé mais la vue restait « en délibération » : fermer
 * demandait de confirmer l'abandon d'une délibération déjà morte, « Annuler »
 * restait proposé et aucun retour n'était possible.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn().mockResolvedValue([]),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));
const annulation = vi.hoisted(() => ({ annulerDeliberation: vi.fn().mockResolvedValue(undefined) }));
vi.mock('./annulerDeliberation', () => ({
  annulerDeliberation: (...args: unknown[]) => annulation.annulerDeliberation(...args),
  couperTransport: (ref: { current: AbortController | null }) => () => { ref.current?.abort(); ref.current = null; },
}));

import { BoardPanel } from './BoardPanel';

function fluxEnPanne() {
  return async function* () {
    yield { type: 'task', content: 'traitement-1' };
    yield { type: 'error', content: 'Ollama ne répond plus.' };
  };
}

describe('#110 : une délibération en erreur n’est plus « en cours »', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation.mockImplementation(fluxEnPanne());
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
  });

  it('après l’erreur, Échap ferme sans demander de confirmation et « Annuler » disparaît', async () => {
    const onClose = vi.fn();
    render(<BoardPanel isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
    await screen.findByTestId('board-result', {}, { timeout: 3000 });
    await screen.findByRole('alert');

    expect(screen.queryByRole('button', { name: /^Annuler$/ })).toBeNull();
    await act(async () => { fireEvent.keyDown(document, { key: 'Escape' }); });
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(onClose).toHaveBeenCalled();
  });
});
