/**
 * B-1837 : un accord mémoire demandé après l'acceptation du message vidait
 * les pièces jointes. Le texte revenait dans le champ, le renvoi partait
 * sans les fichiers. L'échec d'envoi, lui, les remet déjà.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PLACEHOLDER_COMPOSEUR } from '../../lib/etabli';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
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
vi.mock('./SlashCommandsMenu', () => ({
  SlashCommandsMenu: () => null,
  detectSlashCommand: () => false,
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

describe('B-1837 : l’accord mémoire garde les pièces jointes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'], available: true,
    });
    apiMocks.indexFile.mockResolvedValue(undefined);
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [{
        id: 'conv-serveur', title: 'Conversation', messages: [],
        createdAt: new Date(), updatedAt: new Date(), synced: true,
      }],
      currentConversationId: 'conv-serveur', isStreaming: false, queuedPrompt: null,
    });
    usePanelStore.setState({ showSettings: false });
  });

  it('remet les fichiers dans le champ et les renvoie avec la reprise', async () => {
    let appels = 0;
    apiMocks.streamMessage.mockImplementation(() => (async function* () {
      appels += 1;
      if (appels === 1) {
        yield {
          type: 'memory_consent_required',
          conversation_id: 'conv-serveur',
          message_id: 'source-serveur',
          provider: 'ollama',
          purpose: 'documents',
          content: 'Accord requis.',
        };
      } else {
        yield { type: 'text', conversation_id: 'conv-serveur', content: 'Réponse factice.' };
        yield { type: 'done', conversation_id: 'conv-serveur' };
      }
    })());

    const { container } = render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(['contenu'], 'preuve.pdf', { type: 'application/pdf' })] } });
    expect(await screen.findByText('Prêt')).toBeInTheDocument();
    fireEvent.change(input, { target: { value: 'Analyse cette preuve' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));

    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
    expect(apiMocks.streamMessage.mock.calls[0][0]).toMatchObject({ file_paths: ['preuve.pdf'] });
    await waitFor(() => expect(input).toHaveValue('Analyse cette preuve'));
    expect(screen.getByLabelText('Pièces jointes')).toHaveTextContent('Prêt');

    fireEvent.click(screen.getByRole('button', { name: 'Autoriser et envoyer' }));
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(2));
    expect(apiMocks.streamMessage.mock.calls[1][0]).toMatchObject({
      resume_message_id: 'source-serveur',
      file_paths: ['preuve.pdf'],
    });
    expect(useChatStore.getState().currentConversation()?.messages.filter((m) => m.role === 'user')).toHaveLength(1);
  });
});
