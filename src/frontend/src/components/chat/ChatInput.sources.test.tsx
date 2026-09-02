/**
 * Revue 30/08 : l'événement SSE `sources` de la recherche approfondie
 * ne doit plus tomber dans aucune branche.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('ChatInput — sources de la recherche approfondie', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'x', available_models: ['x'], available: true,
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
  });

  it('attache les sources reçues au message assistant', async () => {
    apiMocks.streamDeepResearch.mockImplementation(async function* () {
      yield { type: 'text', content: 'Rapport.' };
      yield {
        type: 'sources',
        content: JSON.stringify([{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' }]),
      };
      yield { type: 'done', content: '' };
    });

    render(<ChatInput />);
    fireEvent.change(await screen.findByTestId('chat-message-input'), {
      target: { value: 'Quelle est l’actualité ?' },
    });
    fireEvent.click(screen.getByTitle('Recherche approfondie (multi-sources)'));

    await waitFor(() => {
      const assistant = useChatStore.getState().conversations[0].messages.find((m) => m.role === 'assistant');
      expect(assistant?.content).toContain('Rapport.');
      expect(assistant?.webSources).toEqual([
        { title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' },
      ]);
    });
  });
});
