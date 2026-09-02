/**
 * Envoyer un message juste après avoir rattaché un projet.
 *
 * Le rattachement persiste la conversation : son identifiant devient celui du
 * serveur. L'envoi attend cette persistance — mais s'il repart ensuite avec
 * l'identifiant qu'il avait AVANT d'attendre, il envoie un identifiant que le
 * serveur ne connaît pas. Le doublon d'hier devient un 404.
 *
 * L'identifiant doit être relu APRÈS l'attente, dans le store, jamais repris
 * de la valeur figée au rendu.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { usePanelStore } from '../../stores/panelStore';
import { PLACEHOLDER_COMPOSEUR } from '../../lib/etabli';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
}));
vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error { status = 500; },
}));

// La persistance déclenchée par le rattachement : elle change l'identifiant
// de la conversation pendant que l'envoi patiente.
const rattachement = vi.hoisted(() => ({
  attendrePersistance: vi.fn(),
  assurerConversationPersistee: vi.fn(async (id: string) => {
    const courante = useChatStore.getState().conversations.find((c) => c.id === id)
      ?? useChatStore.getState().conversations[0];
    return courante?.id ?? id;
  }),
}));
vi.mock('../../lib/rattachementConversation', () => rattachement);

vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({
    saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null,
  }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({
  SlashCommandsMenu: () => null, detectSlashCommand: () => false,
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

async function* fluxVide() {
  yield { type: 'done' as const, content: '' };
}

describe('Envoyer juste après un rattachement de projet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Modèle local disponible : pas d'écran de consentement entre l'envoi et nous.
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama',
      model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'],
      available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    apiMocks.streamMessage.mockImplementation(() => fluxVide());

    useChatStore.setState({
      conversations: [
        {
          id: 'conv-locale',
          title: 'Nouvelle conversation',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          synced: false,
        },
      ] as never,
      currentConversationId: 'conv-locale',
      isStreaming: false,
    });

    // Pendant l'attente, le rattachement persiste la conversation.
    rattachement.attendrePersistance.mockImplementation(async () => {
      useChatStore.setState((etat) => ({
        conversations: etat.conversations.map((c) =>
          c.id === 'conv-locale' ? { ...c, id: 'conv-serveur', synced: true } : c
        ),
        currentConversationId: 'conv-serveur',
      }));
    });
  });

  it('envoie l’identifiant que le serveur connaît, pas celui d’avant l’attente', async () => {
    render(<ChatInput />);
    const champ = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    fireEvent.change(champ, { target: { value: 'Décris-moi la structure du site' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));

    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalled());
    const envoye = apiMocks.streamMessage.mock.calls[0][0];
    expect(envoye.conversation_id).toBe('conv-serveur');
  });
});
