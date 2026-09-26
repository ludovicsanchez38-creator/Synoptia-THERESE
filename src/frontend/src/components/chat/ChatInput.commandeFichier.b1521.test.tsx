/**
 * B-1521 : `/fichier` et `/analyse` lisent un fichier local et l'envoient au
 * modèle. Vers un service en ligne, le composeur ne demandait que l'accord
 * « llm » : la finalité « documents », distincte depuis la revue Soso, était
 * contournée par une simple commande.
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

describe('ChatInput - une commande de fichier est un envoi de document (B-1521)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const stockage: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => stockage[k] ?? null,
      setItem: (k: string, v: string) => { stockage[k] = v; },
      removeItem: (k: string) => { delete stockage[k]; },
      clear: () => { for (const k of Object.keys(stockage)) delete stockage[k]; },
    });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'openai', model: 'gpt-6-astra', available_models: [], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
    useChatStore.setState({
      conversations: [conversation('orion', 'Orion')],
      currentConversationId: 'orion', isStreaming: false, queuedPrompt: null,
    } as never);
  });
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    ['/fichier ~/Documents/devis-roux.pdf'],
    ['Peux-tu lire ceci ?\n/ANALYSE "~/Documents/contrat.docx"'],
  ])('« %s » demande l’accord pour les documents', async (message) => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    await act(async () => { await Promise.resolve(); });
    fireEvent.change(champ(), { target: { value: message } });
    await act(async () => { fireEvent.click(screen.getByTestId('chat-send-btn')); });

    const carte = await screen.findByTestId('chat-cloud-consent');
    expect(carte).toHaveTextContent('contenu intégral des documents joints');
    expect(apiMocks.streamMessage).not.toHaveBeenCalled();
  });
});
