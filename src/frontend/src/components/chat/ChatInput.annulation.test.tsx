/**
 * J1b (31/07/2026) - Le bouton Arrêter doit prévenir le SERVEUR, avec le bon identifiant.
 *
 * `POST /api/chat/cancel/{id}` existe depuis longtemps côté backend, mais aucun
 * code d'interface ne l'appelait : `stopStreaming` se contentait d'un `abort()`
 * local. L'utilisateur voyait la réponse s'arrêter pendant que le serveur
 * continuait de produire et de consommer des tokens.
 *
 * Finding bloquant n°2 de la revue Soso : la première version de ces tests
 * VERROUILLAIT un bug. Une conversation neuve n'est pas encore `synced` ; son
 * identifiant n'est donc pas envoyé, et le backend en crée un autre
 * (`chat.py:588`). Le frontend ne l'apprend qu'au premier événement du flux.
 * Arrêter envoyait l'identifiant LOCAL, absent de `_active_generations` : sur
 * une conversation neuve avec un modèle lent - précisément le cas où l'on veut
 * arrêter - la génération continuait côté serveur.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  cancelGeneration: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Test' }),
}));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {},
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

function poserConversation(options: { synced: boolean }) {
  useChatStore.setState({
    conversations: [
      {
        id: 'conv-locale',
        title: 'Test',
        messages: [],
        createdAt: new Date().toISOString(),
        synced: options.synced,
      },
    ] as never,
    currentConversationId: 'conv-locale',
    isStreaming: true,
  });
}

describe('ChatInput - arrêt de la génération', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'x', available_models: ['x'], available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    poserConversation({ synced: true });
  });

  it('prévient le serveur quand l’utilisateur arrête la réponse', async () => {
    render(<ChatInput />);

    await act(async () => {
      screen.getByLabelText('Arrêter la réponse').click();
    });

    expect(apiMocks.cancelGeneration).toHaveBeenCalledWith('conv-locale');
  });

  it('utilise l’identifiant du SERVEUR quand la conversation vient d’être créée', async () => {
    // Le cas du finding bloquant : conversation neuve, non synchronisée.
    poserConversation({ synced: false });
    useChatStore.setState({ isStreaming: false });

    // Le flux annonce l'identifiant réellement créé par le backend, puis reste
    // ouvert : c'est exactement le moment où l'utilisateur clique sur Arrêter.
    let relacher: () => void = () => {};
    const bloquant = new Promise<void>((resolve) => { relacher = resolve; });
    apiMocks.streamMessage.mockImplementation(async function* () {
      yield { conversation_id: 'conv-serveur', content: 'dé' };
      await bloquant;
    });

    render(<ChatInput />);

    const zone = screen.getByRole('textbox');
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;
      setter?.call(zone, 'Bonjour');
      zone.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await act(async () => {
      zone.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })
      );
    });

    await waitFor(() => {
      expect(screen.queryByLabelText('Arrêter la réponse')).not.toBeNull();
    });

    await act(async () => {
      screen.getByLabelText('Arrêter la réponse').click();
    });

    expect(apiMocks.cancelGeneration).toHaveBeenCalledWith('conv-serveur');
    relacher();
  });

  it('n’échoue pas si l’appel d’annulation lève de façon synchrone', async () => {
    // Cas réel rencontré au run complet de la suite : dès qu'un test monte
    // ChatInput en mockant `services/api` sans définir `cancelGeneration`,
    // l'appel rend `undefined` et le `.catch` explose en TypeError NON
    // CAPTURÉE. Au-delà du bruit de test, le bouton Arrêter ne doit jamais
    // propager d'exception : l'abort local a déjà eu lieu.
    apiMocks.cancelGeneration.mockImplementation(() => {
      throw new Error('module d’API indisponible');
    });
    render(<ChatInput />);

    // `.click()` de jsdom NE propage PAS l'exception à l'appelant : React la
    // relance hors de la pile, où jsdom l'émet en `error` sur window. Un
    // `expect(...).not.toThrow()` autour du clic passerait donc même avec le
    // code cassé — il faut écouter là où l'erreur atterrit vraiment.
    const erreurs: unknown[] = [];
    const capter = (evenement: ErrorEvent) => {
      erreurs.push(evenement.error ?? evenement.message);
      evenement.preventDefault();
    };
    window.addEventListener('error', capter);
    try {
      await act(async () => {
        screen.getByLabelText('Arrêter la réponse').click();
      });
    } finally {
      window.removeEventListener('error', capter);
    }

    expect(erreurs).toEqual([]);
  });

  it('l’arrêt local reste effectif quand le serveur refuse', async () => {
    // Le test précédent de ce cas était creux : il n'observait que l'appel au
    // mock et passait déjà avec l'ancien code (relevé par Soso). Ce qui compte
    // est l'effet : le flux doit être coupé localement même si le serveur ne
    // répond pas, sinon l'interface resterait bloquée en « réponse en cours ».
    //
    // Il faut donc un VRAI flux en cours : poser `isStreaming` à la main ne
    // crée aucun AbortController à interrompre.
    poserConversation({ synced: true });
    useChatStore.setState({ isStreaming: false });
    apiMocks.cancelGeneration.mockRejectedValue(new Error('backend injoignable'));

    // Un vrai `streamMessage` honore le signal d'abandon : sans cela la boucle
    // `for await` ne se dénouerait jamais et le test mesurerait son propre
    // artefact plutôt que le comportement du composant.
    apiMocks.streamMessage.mockImplementation(async function* (
      _payload: unknown,
      signal?: AbortSignal
    ) {
      yield { conversation_id: 'conv-locale', content: 'dé' };
      await new Promise<void>((_resolve, reject) => {
        signal?.addEventListener('abort', () => {
          // Un vrai `fetch` abandonné rejette un DOMException 'AbortError',
          // pas un Error renommé : le composant distingue les deux et ne doit
          // pas partir dans la branche « erreur » (relevé en contre-vérification).
          reject(new DOMException('The operation was aborted.', 'AbortError'));
        });
      });
    });

    render(<ChatInput />);

    const zone = screen.getByRole('textbox');
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;
      setter?.call(zone, 'Bonjour');
      zone.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await act(async () => {
      zone.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })
      );
    });

    await waitFor(() => {
      expect(screen.queryByLabelText('Arrêter la réponse')).not.toBeNull();
    });

    await act(async () => {
      screen.getByLabelText('Arrêter la réponse').click();
    });

    await waitFor(() => {
      expect(useChatStore.getState().isStreaming).toBe(false);
    });
  });
});
