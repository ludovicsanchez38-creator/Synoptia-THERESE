/**
 * B-914 : une synthèse illisible laissait l'indicateur « Synthèse en cours »
 * tourner sans fin ; la seule trace était un console.error. Elle se dit
 * désormais à l'écran, et l'indicateur s'arrête.
 */
import { fireEvent, render, screen } from '@testing-library/react';
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

function fluxSyntheseIllisible() {
  return async function* () {
    yield { type: 'task', content: 'traitement-1' };
    yield { type: 'advisor_start', role: 'analyst', content: '' };
    yield { type: 'advisor_chunk', role: 'analyst', content: 'Avis mesuré.' };
    yield { type: 'advisor_done', role: 'analyst', content: '' };
    yield { type: 'synthesis_start', content: '' };
    yield { type: 'synthesis_chunk', content: 'pas du JSON' };
    yield { type: 'done', content: '' };
  };
}

describe('B-914 : synthèse illisible', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation.mockImplementation(fluxSyntheseIllisible());
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  it('l’indicateur s’arrête et l’échec est dit', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
    const alerte = await screen.findByRole('alert', {}, { timeout: 3000 });
    expect(alerte).toHaveTextContent(/synthèse/i);
    expect(screen.queryByText('Synthèse en cours...')).toBeNull();
  });
});
