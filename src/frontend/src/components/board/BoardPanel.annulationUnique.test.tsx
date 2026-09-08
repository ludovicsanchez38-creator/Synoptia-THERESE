/**
 * B-652 (ronde B, D2) : `processingTaskIdRef` n'était remis à null qu'au
 * démarrage d'une nouvelle délibération. Chaque fermeture de la Décision,
 * même sans rien lancer, rejouait POST /api/processing-tasks/{id}/cancel sur
 * une délibération terminée (409 dans la console, pour toute la session).
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

function fluxQuiAttend() {
  return async function* () {
    yield { type: 'task', content: 'traitement-1' };
    await new Promise<void>(() => {});
  };
}

describe('B-652 : une demande d’arrêt par délibération, jamais sur une délibération finie', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation.mockImplementation(fluxQuiAttend());
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
  });

  it('après « Annuler », fermer puis rouvrir et refermer n’envoie plus l’identifiant', async () => {
    const onClose = vi.fn();
    const { rerender } = render(<BoardPanel isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
    await screen.findByTestId('board-result', {}, { timeout: 3000 });

    fireEvent.click(screen.getByRole('button', { name: /^Annuler$/ }));
    expect(annulation.annulerDeliberation).toHaveBeenLastCalledWith('traitement-1', expect.any(Function));

    await act(async () => { fireEvent.keyDown(document, { key: 'Escape' }); });
    rerender(<BoardPanel isOpen={false} onClose={onClose} />);
    rerender(<BoardPanel isOpen onClose={onClose} />);
    await act(async () => { fireEvent.keyDown(document, { key: 'Escape' }); });

    const identifiants = annulation.annulerDeliberation.mock.calls.slice(1).map((c) => c[0]);
    expect(identifiants.every((id) => id === null)).toBe(true);
  });
});
