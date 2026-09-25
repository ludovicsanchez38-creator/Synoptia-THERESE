/**
 * B-1471 (recette P-146, lot 5, KO-4b) : dans une conversation, « / » ouvre
 * le menu « Commandes disponibles » ; Échap devait fermer ce seul menu, il
 * quittait aussi la conversation.
 *
 * Cause, vérifiée dans le navigateur : le composeur fermait le menu dans son
 * propre onKeyDown. Pour une vraie touche, le navigateur vide les
 * microtâches entre deux écouteurs : React valide la fermeture, l'effet du
 * menu retire son gestionnaire de la pile d'Échap, et la cascade de la coque
 * (écouteur sur window, appelé ensuite) ne trouve plus que la conversation.
 * Un Échap synthétique (un seul appel JS, sans ce point de contrôle) ne
 * fermait que le menu : c'est ce qui laissait les tests verts.
 *
 * Le test rejoue ce point de contrôle : un écouteur sur document, placé entre
 * la racine React et window, valide le rendu en attente (flushSync) avant la
 * cascade.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { flushSync } from 'react-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  cancelGeneration: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' }),
}));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {
    status = 500;
  },
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('B-1471 : Échap avec le menu « / » ouvert ne ferme que le menu', () => {
  const conversationQuittee = vi.fn();
  // La cascade de la coque, réduite à ce qui compte ici : la pile d'abord,
  // la conversation ensuite (ConversationCanvasPrototype, consommeEchapUnifie).
  const cascadeDeLaCoque = (e: KeyboardEvent) => {
    if (e.key !== 'Escape') return;
    if (runTopEscapeHandler()) return;
    conversationQuittee();
  };
  // Le point de contrôle des microtâches d'une vraie touche.
  const pointDeControle = (e: KeyboardEvent) => {
    if (e.key === 'Escape') flushSync(() => {});
  };

  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: ['qwen3:8b'], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    document.addEventListener('keydown', pointDeControle);
    window.addEventListener('keydown', cascadeDeLaCoque);
  });
  afterEach(() => {
    document.removeEventListener('keydown', pointDeControle);
    window.removeEventListener('keydown', cascadeDeLaCoque);
  });

  it('la conversation reste ouverte et le menu se ferme', async () => {
    render(<ChatInput />);
    const champ = await screen.findByTestId('chat-message-input') as HTMLTextAreaElement;
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(champ, { target: { value: '/' } });
    await screen.findByText('Commandes disponibles');

    // Hors act : l'ordonnancement réel de React, comme pour une vraie touche.
    champ.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));

    await waitFor(() => expect(screen.queryByText('Commandes disponibles')).not.toBeInTheDocument());
    expect(conversationQuittee, 'Échap a quitté la conversation au lieu du seul menu').not.toHaveBeenCalled();
  });
});
