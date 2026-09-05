import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mockStream = vi.fn();
const mockCancelTask = vi.fn();

vi.mock('../../services/api/agents', () => ({
  streamAgentRequest: (...args: unknown[]) => mockStream(...args),
  cancelTask: (...args: unknown[]) => mockCancelTask(...args),
  getAgentConfig: vi.fn().mockResolvedValue({ source_path: '/tmp/depot', agents: [] }),
}));

import { useAtelierStore } from '../../stores/atelierStore';
import { AtelierPanel } from './AtelierPanel';

/** Un flux qui s'ouvre, n'émet rien, et sort quand on l'avorte — comme le vrai
 *  streamAgentRequest. Un mock qui ignorerait le signal testerait un monde qui
 *  n'existe pas. */
function fluxMuet(_message?: string, _chemin?: string, signal?: AbortSignal): AsyncGenerator<unknown> {
  return (async function* () {
    await new Promise<void>((resolve) => {
      if (signal?.aborted) return resolve();
      signal?.addEventListener('abort', () => resolve(), { once: true });
    });
    // Jamais atteint : le flux se ferme sans avoir rien emis. Presence exigee
    // par la regle require-yield, qui refuse un generateur sans yield.
    if (signal?.reason === '__jamais__') yield undefined;
  })();
}

async function lancerUneMission(texte: string) {
  const champ = screen.getByPlaceholderText(/Posez une question/i);
  fireEvent.change(champ, { target: { value: texte } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  await waitFor(() => screen.getByText('Confirmer et lancer'));
  await act(async () => {
    fireEvent.click(screen.getByText('Confirmer et lancer'));
  });
}

describe('Atelier : une mission à la fois', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAtelierStore.setState({ isOpen: true, activeView: 'chat', messages: [], isStreaming: false });
    mockStream.mockImplementation((...args: unknown[]) => fluxMuet(...(args as [string, string, AbortSignal])));
  });

  // Une mission encore vivante à la fin d'un test se ferme en retard, APRÈS le
  // démontage de jsdom : son `finally` appelait setState sur un `window` disparu
  // (« window is not defined », promesse non gérée, CI rouge du 05/09/2026).
  // On annule et on laisse la fermeture retardée tomber pendant que le DOM vit.
  afterEach(async () => {
    await act(async () => {
      const annuler = screen.queryByTitle('Annuler');
      if (annuler) fireEvent.click(annuler);
      await new Promise((r) => setTimeout(r, 60));
    });
    cleanup();
  });

  // Relevé par la lecture du lot WP-060, reproduit ici. `runMission` écrivait
  // `abortRef.current` sans garde, et `isStreaming` ne passe à vrai qu'au
  // PREMIER CHUNK reçu (atelierStore). Entre le lancement et ce premier chunk,
  // la saisie restait ouverte et le bouton d'annulation absent : deux missions
  // enchaînées, la seconde écrasait le jeton de la première, puis le `finally`
  // de la première effaçait celui de la seconde, devenue inarrêtable.
  it('verrouille la saisie dès le lancement, sans attendre le premier chunk', async () => {
    render(<AtelierPanel />);
    await lancerUneMission('Première mission');

    expect(mockStream).toHaveBeenCalledTimes(1);
    // Le flux n'a rien émis : isStreaming est encore faux dans le store.
    expect(useAtelierStore.getState().isStreaming).toBe(false);
    // Et pourtant la saisie doit déjà être fermée.
    expect(screen.getByPlaceholderText(/Posez une question/i)).toBeDisabled();
  });

  it('refuse une seconde mission tant que la première tient le jeton', async () => {
    render(<AtelierPanel />);
    await lancerUneMission('Première mission');

    // Le premier jet de ce test s'arrêtait au clic « Envoyer » et passait déjà :
    // `onSend` ne fait que poser le message en attente, c'est « Confirmer et
    // lancer » qui appelle runMission. Un test vert qui ne va pas jusqu'au bout
    // du parcours ne prouve rien.
    //
    // Une fois la mission lancée, il n'y a PLUS de bouton « Envoyer » : la
    // seconde mission est hors d'atteinte, et l'annulation est offerte à la
    // place. C'est ce que l'utilisateur doit voir.
    expect(screen.queryByTitle('Envoyer')).not.toBeInTheDocument();
    expect(screen.getByTitle('Annuler')).toBeInTheDocument();
    expect(mockStream).toHaveBeenCalledTimes(1);
  });
  // Le verrou de saisie est de l'interface ; il tombe si un chemin atteint
  // runMission sans passer par le champ. Le double-clic sur « Confirmer et
  // lancer » est ce chemin : les deux clics partent avant le re-rendu qui
  // retire le bouton. Sans la garde sur le jeton, deux flux s'ouvrent.
  it('un double-clic sur la confirmation ne lance qu’une mission', async () => {
    render(<AtelierPanel />);
    const champ = screen.getByPlaceholderText(/Posez une question/i);
    fireEvent.change(champ, { target: { value: 'Mission doublement confirmée' } });
    fireEvent.click(screen.getByTitle('Envoyer'));
    await waitFor(() => screen.getByText('Confirmer et lancer'));

    const bouton = screen.getByText('Confirmer et lancer');
    await act(async () => {
      fireEvent.click(bouton);
      fireEvent.click(bouton);
    });

    expect(mockStream).toHaveBeenCalledTimes(1);
  });
  // Le scénario d'origine, une fois la course fermée : annuler puis relancer.
  // Le `finally` de la mission avortée s'exécute APRÈS le lancement de la
  // suivante. S'il nettoie aveuglément, il efface le jeton de la seconde, qui
  // devient inarrêtable — le bouton d'annulation ne pilote plus rien.
  it('la mission relancée après une annulation garde son propre jeton', async () => {
    render(<AtelierPanel />);
    await lancerUneMission('Mission annulée');

    await act(async () => {
      fireEvent.click(screen.getByTitle('Annuler'));
    });
    await waitFor(() => expect(screen.getByTitle('Envoyer')).toBeInTheDocument());

    await lancerUneMission('Mission relancée');

    expect(mockStream).toHaveBeenCalledTimes(2);
    // Le jeton de la seconde tient : la saisie reste fermée et l'annulation offerte.
    expect(screen.getByPlaceholderText(/Posez une question/i)).toBeDisabled();
    expect(screen.getByTitle('Annuler')).toBeInTheDocument();
  });
  // Le `finally` d'un flux ne tombe pas au moment de l'abort : la fermeture
  // réseau prend un tour de boucle. Ici la mission relancée démarre AVANT que
  // la précédente n'ait fini de se clore. Sans la garde `abortRef === son
  // propre contrôleur`, ce `finally` tardif efface le jeton de la mission
  // vivante, qui devient inarrêtable — le défaut d'origine, dans sa dernière
  // forme atteignable.
  it('un flux qui se ferme en retard ne vole pas le jeton de la mission suivante', async () => {
    mockStream.mockImplementation((..._args: unknown[]) => {
      const signal = _args[2] as AbortSignal | undefined;
      return (async function* () {
        await new Promise<void>((resolve) => {
          if (signal?.aborted) return void setTimeout(resolve, 20);
          signal?.addEventListener('abort', () => setTimeout(resolve, 20), { once: true });
        });
        if (signal?.reason === '__jamais__') yield undefined;
      })();
    });

    render(<AtelierPanel />);
    await lancerUneMission('Mission lente à se fermer');
    await act(async () => {
      fireEvent.click(screen.getByTitle('Annuler'));
    });
    await waitFor(() => expect(screen.getByTitle('Envoyer')).toBeInTheDocument());
    await lancerUneMission('Mission vivante');

    // La fermeture retardée de la première tombe maintenant.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 60));
    });

    expect(screen.getByPlaceholderText(/Posez une question/i)).toBeDisabled();
    expect(screen.getByTitle('Annuler')).toBeInTheDocument();
  });
});
