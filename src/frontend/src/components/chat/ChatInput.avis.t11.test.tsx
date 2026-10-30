/**
 * Tour 11 (relecture 10) : un avis système arrive dans un événement `notice`
 * distinct ; il est affiché avec le message, jamais ajouté à son contenu.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';

const AVIS = '*(1 ancienne préférence ou correction attend ta confirmation dans Mémoire.)*';
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
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('ChatInput : avis hors du contenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'gemma4-tia:latest', available_models: ['gemma4-tia:latest'], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    apiMocks.streamMessage.mockImplementation(async function* () {
      yield { type: 'notice', content: AVIS, conversation_id: 'conv-serveur' };
      yield { type: 'text', content: 'Bonjour Paul,', conversation_id: 'conv-serveur' };
      yield { type: 'done', content: '', conversation_id: 'conv-serveur', message_id: 'm1' };
    });
  });

  it('range l’avis à part et garde le contenu intact', async () => {
    render(<ChatInput />);
    const zone = (await screen.findByTestId('chat-message-input')) as HTMLTextAreaElement;
    await waitFor(() => expect(zone).not.toBeDisabled());
    fireEvent.change(zone, { target: { value: 'Écris un mail à Paul.' } });
    fireEvent.keyDown(zone, { key: 'Enter', code: 'Enter' });
    await waitFor(() => {
      const reponse = useChatStore.getState().conversations.flatMap(c => c.messages).find(m => m.role === 'assistant');
      expect(reponse?.isStreaming).toBeFalsy();
      expect(reponse?.content).toBe('Bonjour Paul,');
      expect(reponse?.avis).toEqual([AVIS]);
    });
  });
});
