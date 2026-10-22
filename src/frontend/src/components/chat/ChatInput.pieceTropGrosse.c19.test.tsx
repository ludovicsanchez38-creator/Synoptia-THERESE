// B-1107 : le préambule du moteur reste visible après le flux du modèle.
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  cancelGeneration: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' }),
}));
vi.mock('../../services/api', () => ({ ...apiMocks, ApiError: class ApiError extends Error { status = 500; } }));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('ChatInput - pièce jointe trop volumineuse (B-1107)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => undefined, removeItem: () => undefined, clear: () => undefined });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'gemma4-tia:latest', available_models: [], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null } as never);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('conserve le nom et la limite dans la réponse après le message du modèle', async () => {
    apiMocks.streamMessage.mockImplementation(async function* () {
      yield { type: 'text', content: 'inventaire.txt : le fichier dépasse la limite de 50 Mo.\n\n', conversation_id: 'conv-1' };
      yield { type: 'text', content: 'Réponse du modèle.', conversation_id: 'conv-1' };
      yield { type: 'done', conversation_id: 'conv-1' };
    });
    render(<ChatInput />);
    const champ = await screen.findByTestId('chat-message-input');
    fireEvent.change(champ, { target: { value: 'Lis mon inventaire.' } });
    fireEvent.keyDown(champ, { key: 'Enter' });

    await waitFor(() => {
      const messages = useChatStore.getState().conversations[0]?.messages ?? [];
      const reponse = messages.find((m) => m.role === 'assistant');
      expect(reponse?.content).toContain('inventaire.txt');
      expect(reponse?.content).toContain('50 Mo');
      expect(reponse?.content).toContain('Réponse du modèle.');
    });

  });
});
