/**
 * B-1172 : en mode souverain, le Board ne propose ni n'envoie aucun modèle Ollama Cloud.
 *
 * Règle (B-1156, board.py:457-464) : en mode souverain, un modèle Ollama Cloud
 * est refusé par le moteur ; le défaut choisi par le moteur ignore les modèles
 * Cloud (llm.py detect_default_ollama_model). L'écran du Board, lui, garde tous
 * les modèles de la sonde, les trie par taille, déclare le premier pour les
 * cinq conseillers (B-110) et affiche « Tout reste sur cette machine ».
 * On mesure ce que « Confirmer et lancer » envoie réellement au moteur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn().mockResolvedValue([]),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
  listAdvisors: vi.fn().mockResolvedValue([]),
  getOllamaStatus: vi.fn(),
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

const gib = 1024 ** 3;

function fluxQuiAttend() {
  return async function* () {
    yield { type: 'task', content: 'traitement-1' };
    await new Promise<void>(() => {});
  };
}

function sonde(models: Array<{ name: string; size: number | null }>) {
  return {
    available: true,
    base_url: 'http://127.0.0.1:11434',
    models: models.map((m) => ({ ...m, modified_at: null, digest: null })),
    error: null,
  };
}

async function lancerSouverain() {
  render(<BoardPanel isOpen onClose={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Souverain/ }));
  fireEvent.change(screen.getByLabelText('Question soumise au Board'), {
    target: { value: 'Dois-je passer ma société en SASU cette année ?' },
  });
  // Laisse la sonde et la déclaration B-110 se poser.
  await waitFor(() => expect(screen.getAllByLabelText('Modèle du conseiller analyst').length).toBeGreaterThan(0));
  const select = screen.getAllByLabelText('Modèle du conseiller analyst')[0] as HTMLSelectElement;
  const optionsProposees = Array.from(select.options).map((o) => o.value);
  const valeurAffichee = select.value;
  fireEvent.click(screen.getByTestId('board-submit-btn'));
  const confirmation = await screen.findByTestId('board-confirmation');
  const texteConfirmation = confirmation.textContent ?? '';
  fireEvent.click(screen.getByRole('button', { name: /Confirmer et lancer/ }));
  await waitFor(() => expect(apiMocks.streamDeliberation).toHaveBeenCalledTimes(1));
  const envoye = apiMocks.streamDeliberation.mock.calls[0][0] as { ollama_models?: Record<string, string> };
  return { optionsProposees, valeurAffichee, texteConfirmation, envoye };
}

describe('B-1172 : Board souverain et modèles Ollama Cloud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listBoardDecisions.mockResolvedValue([]);
    apiMocks.streamDeliberation.mockImplementation(fluxQuiAttend());
  });

  it('n’envoie aucun modèle Ollama Cloud au moteur en mode souverain (taille rapportée petite)', async () => {
    apiMocks.getOllamaStatus.mockResolvedValue(sonde([
      { name: 'qwen3:8b', size: 5 * gib },
      { name: 'kimi-k2.6:cloud', size: 1000 },
    ]));
    const r = await lancerSouverain();
    const etat = {
      optionsProposees: r.optionsProposees,
      valeurAffichee: r.valeurAffichee,
      confirmationDitLocal: /reste sur cette machine/i.test(r.texteConfirmation),
      modelesEnvoyes: r.envoye.ollama_models,
    };
    expect(etat).toEqual({
      optionsProposees: ['qwen3:8b'],
      valeurAffichee: 'qwen3:8b',
      confirmationDitLocal: true,
      modelesEnvoyes: {
        analyst: 'qwen3:8b', strategist: 'qwen3:8b', devil: 'qwen3:8b',
        pragmatic: 'qwen3:8b', visionary: 'qwen3:8b',
      },
    });
  });

  it('même mesure quand la sonde ne rapporte aucune taille pour le modèle Cloud (size null → 0)', async () => {
    apiMocks.getOllamaStatus.mockResolvedValue(sonde([
      { name: 'qwen3:8b', size: 5 * gib },
      { name: 'gpt-oss:120b-cloud', size: null },
    ]));
    const r = await lancerSouverain();
    expect({ valeurAffichee: r.valeurAffichee, modelesEnvoyes: r.envoye.ollama_models }).toEqual({
      valeurAffichee: 'qwen3:8b',
      modelesEnvoyes: {
        analyst: 'qwen3:8b', strategist: 'qwen3:8b', devil: 'qwen3:8b',
        pragmatic: 'qwen3:8b', visionary: 'qwen3:8b',
      },
    });
  });

  it('seul un modèle Cloud installé : le mode souverain ne se déclare pas disponible', async () => {
    apiMocks.getOllamaStatus.mockResolvedValue(sonde([{ name: 'kimi-k2.6:cloud', size: 1000 }]));
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    await waitFor(() => expect(apiMocks.getOllamaStatus).toHaveBeenCalled());
    const souverain = await screen.findByRole('button', { name: /Souverain/ });
    // Attendu : aucun modèle local, donc le mode souverain est grisé
    // (« Ollama non disponible ») et aucune promesse « Tout reste sur cette machine ».
    await waitFor(() => {
      expect({
        souverainActivable: !(souverain as HTMLButtonElement).disabled,
        titre: souverain.getAttribute('title'),
      }).toEqual({
        souverainActivable: false,
        // B-1215 : Ollama tourne ; ce qui manque, c'est un modèle local.
        titre: 'Aucun modèle local installé : les modèles Ollama Cloud partent en ligne',
      });
    });
    fireEvent.click(souverain);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), {
      target: { value: 'Dois-je passer ma société en SASU cette année ?' },
    });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    expect(screen.queryByText(/Tout reste sur cette machine/)).toBeNull();
  });

  it('témoin : sans modèle Cloud, les cinq conseillers partent sur le modèle local', async () => {
    apiMocks.getOllamaStatus.mockResolvedValue(sonde([{ name: 'qwen3:8b', size: 5 * gib }]));
    const r = await lancerSouverain();
    expect(r.envoye.ollama_models).toEqual({
      analyst: 'qwen3:8b', strategist: 'qwen3:8b', devil: 'qwen3:8b',
      pragmatic: 'qwen3:8b', visionary: 'qwen3:8b',
    });
  });
});
