/**
 * J1b (31/07/2026) - Le bouton Arrêter doit prévenir le serveur.
 *
 * `POST /api/chat/cancel/{id}` existe depuis longtemps côté backend, mais aucun
 * code d'interface ne l'appelait : `stopStreaming` se contentait d'un `abort()`
 * local. L'utilisateur voyait la réponse s'arrêter pendant que le serveur
 * continuait de produire et de consommer des tokens.
 */
import { act, render, screen } from '@testing-library/react';
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
}));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {},
}));
vi.mock('../../hooks/useGhostText', () => ({
  useGhostText: () => ({ suggestion: '', accept: vi.fn(), dismiss: vi.fn() }),
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

describe('ChatInput - arrêt de la génération', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'x', available_models: ['x'], available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [{ id: 'conv-1', title: 'Test', messages: [], createdAt: new Date().toISOString() }] as never,
      currentConversationId: 'conv-1',
      isStreaming: true,
    });
  });

  it('prévient le serveur quand l’utilisateur arrête la réponse', async () => {
    render(<ChatInput />);

    await act(async () => {
      screen.getByLabelText('Arrêter la réponse').click();
    });

    expect(apiMocks.cancelGeneration).toHaveBeenCalledWith('conv-1');
  });

  it('n’échoue pas si le serveur refuse l’annulation', async () => {
    apiMocks.cancelGeneration.mockRejectedValue(new Error('backend injoignable'));
    render(<ChatInput />);

    await act(async () => {
      screen.getByLabelText('Arrêter la réponse').click();
    });

    // L'arrêt local doit rester effectif même si le serveur ne répond pas :
    // sinon l'interface resterait bloquée en « réponse en cours ».
    expect(apiMocks.cancelGeneration).toHaveBeenCalled();
  });

  it('n’échoue pas si l’appel d’annulation lève de façon synchrone', async () => {
    // Cas réel rencontré au run complet de la suite : dès qu'un test monte
    // ChatInput en mockant `services/api` sans définir `cancelGeneration`,
    // l'appel rend `undefined` et le `.catch` explose en TypeError NON
    // CAPTURÉE. Vitest impute alors l'erreur au fichier en cours d'exécution
    // et fait échouer des tests étrangers (« false positive tests »).
    //
    // Au-delà du bruit de test, c'est un vrai défaut : le bouton Arrêter ne
    // doit jamais propager d'exception. L'abort local a déjà eu lieu, prévenir
    // le serveur est un bonus qui ne peut pas casser le geste de l'utilisateur.
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
});
