/**
 * P-159 : l'événement done pose le contexte transmis sur la réponse.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  createConversation: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error { status = 500; },
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({
    saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null,
  }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('ChatInput — contexte transmis (P-159)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'local', available_models: ['local'], available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [{
        id: 'conv-1', title: 'Test', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: true,
      }],
      currentConversationId: 'conv-1',
      isStreaming: false,
      queuedPrompt: null,
    });
    apiMocks.streamMessage.mockImplementation(async function* () {
      yield { type: 'text', content: 'Voilà.' };
      yield {
        type: 'done',
        content: '',
        contexte: { messages_relus: 12, messages_transmis: 12 },
      };
    });
  });

  it('attache au message assistant le contexte annoncé par le flux', async () => {
    render(<ChatInput />);
    fireEvent.change(await screen.findByTestId('chat-message-input'), {
      target: { value: 'Bonjour' },
    });
    fireEvent.click(screen.getByTestId('chat-send-btn'));

    await waitFor(() => {
      const assistant = useChatStore.getState().conversations[0].messages.find((m) => m.role === 'assistant');
      expect(assistant?.contexte).toEqual({ messages_relus: 12, messages_transmis: 12 });
    });
  });
});
