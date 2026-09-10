/**
 * Revue Grok du diff 0.70.0 (P2) : #110 masque le dialogue de fermeture dès
 * qu'une erreur arrive, mais `fermetureDemandee` restait vrai. Échap pendant le
 * flux, puis erreur, puis nouvelle délibération : le bandeau « Une délibération
 * est en cours » réapparaissait tout seul, et « Annuler et fermer » jetait le
 * nouveau run.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(), listBoardDecisions: vi.fn().mockResolvedValue([]), getBoardDecision: vi.fn(), deleteBoardDecision: vi.fn(),
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

const signal = vi.hoisted(() => ({ liberer: undefined as undefined | (() => void) }));

async function lancer() {
  fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
  fireEvent.click(screen.getByTestId('board-submit-btn'));
  fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
  await screen.findByTestId('board-result', {}, { timeout: 3000 });
}

describe('Grok 0.70.0 P2 : la demande de fermeture ne survit pas à l’erreur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation
      .mockImplementationOnce(async function* () {
        yield { type: 'task', content: 'traitement-1' };
        await new Promise<void>((resolve) => { signal.liberer = resolve; });
        yield { type: 'error', content: 'Ollama ne répond plus.' };
      })
      .mockImplementation(async function* () {
        yield { type: 'task', content: 'traitement-2' };
        await new Promise<void>(() => {});
      });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
  });

  it('Échap pendant le flux, erreur, retour, relance : aucun bandeau de fermeture spontané', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    await lancer();
    await act(async () => { fireEvent.keyDown(document, { key: 'Escape' }); });
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();

    await act(async () => { signal.liberer?.(); await new Promise((r) => setTimeout(r, 50)); });
    await screen.findByRole('alert');
    expect(screen.queryByRole('alertdialog')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    await lancer();
    expect(screen.queryByRole('alertdialog')).toBeNull();
  });
});
