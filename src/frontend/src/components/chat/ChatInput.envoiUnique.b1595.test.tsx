/**
 * B-1595 (régression de B-1530) : un message qui contient une variable
 * attend l'aperçu des variables avant de passer en « réponse en cours ».
 * Pendant cette attente, un double clic ou deux Entrée l'envoyaient deux
 * fois, et le premier flux n'était plus arrêtable.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
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
const variablesMocks = vi.hoisted(() => ({ previewVariables: vi.fn() }));
vi.mock('../../services/api/variables', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...variablesMocks,
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

const conversation = (id: string, title: string) => ({
  id, title, messages: [], messageCount: 2, createdAt: new Date(), updatedAt: new Date(), synced: true,
});

function champ() {
  return screen.getByTestId('chat-message-input') as HTMLTextAreaElement;
}

describe('B-1595 : un message à variable ne part qu’une fois', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const stockage: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => stockage[k] ?? null,
      setItem: (k: string, v: string) => { stockage[k] = v; },
      removeItem: (k: string) => { delete stockage[k]; },
      clear: () => { for (const k of Object.keys(stockage)) delete stockage[k]; },
    });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: [], available: true });
    apiMocks.streamMessage.mockImplementation(async function* () { /* aucun événement */ });
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
    useChatStore.setState({
      conversations: [conversation('orion', 'Orion')],
      currentConversationId: 'orion', isStreaming: false, queuedPrompt: null,
    } as never);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('deux clics pendant l’aperçu des variables n’envoient qu’un message', async () => {
    variablesMocks.previewVariables.mockImplementation(async (texte: string) => {
      await new Promise((r) => setTimeout(r, 80));
      return { resolved: texte.replace('{client}', 'Hélène'), unknown: [], errors: [], variables_revision: 'r1' };
    });
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    await act(async () => { await Promise.resolve(); });
    fireEvent.change(champ(), { target: { value: 'Relance {client}' } });
    await act(async () => { await new Promise((r) => setTimeout(r, 150)); });

    await act(async () => {
      fireEvent.click(screen.getByTestId('chat-send-btn'));
      fireEvent.click(screen.getByTestId('chat-send-btn'));
      await new Promise((r) => setTimeout(r, 300));
    });

    expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1);
  });
});
