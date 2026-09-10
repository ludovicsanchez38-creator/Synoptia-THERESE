/**
 * Cycle 6, lecteur #125 (ChatInput.tsx) : après « Arrêter la réponse », le
 * catch restaurait saisie, pièces et brouillon AVANT de reconnaître
 * l'AbortError : le message déjà dans la conversation revenait dans le
 * composeur, invitant à l'envoyer deux fois.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(), setLLMConfig: vi.fn(), streamMessage: vi.fn(), streamDeepResearch: vi.fn(), indexFile: vi.fn(),
  cancelGeneration: vi.fn(), createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Test' }),
}));
vi.mock('../../services/api', () => ({ ...apiMocks, ApiError: class ApiError extends Error {} }));
const autosave = vi.hoisted(() => ({ saveDraft: vi.fn() }));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: autosave.saveDraft, restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('#125 : un arrêt volontaire ne remet pas le message dans le composeur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'x', available_models: ['x'], available: true });
    apiMocks.cancelGeneration.mockResolvedValue(undefined);
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [{ id: 'conv-locale', title: 'Test', messages: [], createdAt: new Date().toISOString(), synced: true }] as never,
      currentConversationId: 'conv-locale', isStreaming: false,
    });
    apiMocks.streamMessage.mockImplementation(async function* (_payload: unknown, signal?: AbortSignal) {
      yield { conversation_id: 'conv-locale', content: 'dé' };
      await new Promise<void>((_resolve, reject) => {
        signal?.addEventListener('abort', () => reject(new DOMException('The operation was aborted.', 'AbortError')));
      });
    });
  });

  it('après Arrêter, le champ reste vide et aucun brouillon n’est réécrit', async () => {
    render(<ChatInput />);
    const zone = screen.getByRole('textbox') as HTMLTextAreaElement;
    await act(async () => {
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set?.call(zone, 'Bonjour');
      zone.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await act(async () => {
      zone.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
    });
    const arreter = await screen.findByRole('button', { name: /Arrêter/ });
    autosave.saveDraft.mockClear();
    await act(async () => { arreter.click(); });
    await waitFor(() => expect(useChatStore.getState().isStreaming).toBe(false));
    expect(zone.value).toBe('');
    expect(autosave.saveDraft).not.toHaveBeenCalledWith('Bonjour');
  });
});
