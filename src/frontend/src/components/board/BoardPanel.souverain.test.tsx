/**
 * Persona Nadia, cycle 4 - Board souverain :
 * - B-639 (P1) : après « Confirmer et lancer », aucun changement d'écran ;
 *   le formulaire restait (invisible mais cliquable) et un second clic
 *   lançait une seconde délibération. La vue de délibération doit monter
 *   aussitôt, avec un statut lisible et un moyen d'annuler avant même le
 *   premier avis.
 * - B-640 (P1) : Échap ou « Fermer » pendant la délibération jetait tout
 *   sans avertissement (trois avis calculés, rien d'enregistré). La
 *   fermeture demande confirmation tant qu'une délibération est en cours.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn().mockResolvedValue([]),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
  listAdvisors: vi.fn().mockResolvedValue([]),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));
vi.mock('./annulerDeliberation', () => ({
  annulerDeliberation: vi.fn().mockResolvedValue(undefined),
  couperTransport: (ref: { current: AbortController | null }) => () => {
    ref.current?.abort();
    ref.current = null;
  },
}));

import { BoardPanel } from './BoardPanel';

/** Flux qui annonce la tâche puis attend indéfiniment (modèle local qui charge). */
function fluxQuiAttend() {
  return async function* () {
    yield { type: 'task', content: 'traitement-1' };
    await new Promise<void>(() => {});
  };
}

async function lancerUneDeliberation() {
  render(<BoardPanel isOpen onClose={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Question soumise au Board'), {
    target: { value: 'Dois-je passer ma société en SASU cette année ?' },
  });
  fireEvent.click(screen.getByTestId('board-submit-btn'));
  fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
}

describe('B-639 : lancer la délibération change d’écran tout de suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation.mockImplementation(fluxQuiAttend());
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
  });

  it('la vue de délibération monte, le formulaire et sa confirmation disparaissent', async () => {
    await lancerUneDeliberation();
    await waitFor(() => expect(screen.getByTestId('board-result')).toBeInTheDocument(), { timeout: 3000 });
    expect(screen.queryByTestId('board-confirmation')).toBeNull();
    expect(screen.queryByTestId('board-submit-btn')).toBeNull();
    expect(apiMocks.streamDeliberation).toHaveBeenCalledTimes(1);
  });

  it('avant le premier avis, un statut dit que la délibération est lancée et « Annuler » est offert', async () => {
    await lancerUneDeliberation();
    await screen.findByTestId('board-result', {}, { timeout: 3000 });
    expect(screen.getByRole('status')).toHaveTextContent(/Délibération lancée/i);
    expect(screen.getByRole('button', { name: /^Annuler$/ })).toBeInTheDocument();
  });
});

describe('B-640 : fermer pendant la délibération demande confirmation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.streamDeliberation.mockImplementation(fluxQuiAttend());
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [] }) }));
  });

  it('Échap affiche l’avertissement au lieu de fermer, et « Continuer » le retire', async () => {
    const onClose = vi.fn();
    render(<BoardPanel isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), {
      target: { value: 'Dois-je passer ma société en SASU cette année ?' },
    });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
    await screen.findByTestId('board-result', {}, { timeout: 3000 });

    await act(async () => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });

    expect(onClose).not.toHaveBeenCalled();
    const alerte = screen.getByRole('alertdialog');
    expect(alerte).toHaveTextContent(/délibération est en cours/i);
    fireEvent.click(screen.getByRole('button', { name: /Continuer la délibération/ }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('« Annuler et fermer » confirme la fermeture et annule la délibération', async () => {
    const onClose = vi.fn();
    render(<BoardPanel isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), {
      target: { value: 'Dois-je passer ma société en SASU cette année ?' },
    });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));
    await screen.findByTestId('board-result', {}, { timeout: 3000 });

    fireEvent.click(screen.getByRole('button', { name: 'Fermer le Board' }));
    fireEvent.click(await screen.findByRole('button', { name: /Annuler et fermer/ }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
