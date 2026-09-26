/**
 * B-1514 (R-109-2) : « Arrêter » avec un message en file pouvait arrêter la
 * génération du message en file. L'arrêt visait « la génération courante de
 * la conversation » sans être attendu, et la file partait 50 ms après la fin
 * du flux : la demande d'arrêt, arrivée après, frappait la nouvelle réponse.
 * L'arrêt vise désormais la génération affichée, par son identifiant, et la
 * file attend que la demande soit traitée.
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
  annulerTraitement: vi.fn(),
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

function fluxAnnulable(generationId: string) {
  return (_requete: unknown, signal?: AbortSignal) => (async function* () {
    yield { type: 'generation', generation_id: generationId };
    yield { type: 'text', content: 'Réponse en cours' };
    await new Promise<void>((_resolve, reject) => {
      signal?.addEventListener('abort', () => reject(new DOMException('Arrêt', 'AbortError')));
    });
  })();
}

describe('ChatInput - arrêter avec un message en file (B-1514)', () => {
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
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
    useChatStore.setState({
      conversations: [conversation('orion', 'Orion')],
      currentConversationId: 'orion', isStreaming: false, queuedPrompt: null,
    } as never);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('l’arrêt vise la génération affichée, et la file attend qu’il soit traité', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    apiMocks.streamMessage.mockImplementationOnce(fluxAnnulable('gen-A'));
    fireEvent.change(champ(), { target: { value: 'Premier message' } });
    await act(async () => { fireEvent.click(screen.getByTestId('chat-send-btn')); });

    fireEvent.change(champ(), { target: { value: 'Message en file' } });
    await act(async () => { fireEvent.keyDown(champ(), { key: 'Enter' }); });
    expect(useChatStore.getState().queuedPrompt).toBe('Message en file');

    let traiter!: () => void;
    apiMocks.annulerTraitement.mockReturnValue(new Promise<void>((resolve) => { traiter = resolve; }));
    apiMocks.streamMessage.mockImplementationOnce(fluxAnnulable('gen-B'));
    await act(async () => { fireEvent.click(screen.getByLabelText('Arrêter la réponse')); });

    expect(apiMocks.annulerTraitement).toHaveBeenCalledWith('gen-A');
    expect(apiMocks.cancelGeneration).not.toHaveBeenCalled();
    await act(async () => { await new Promise((r) => setTimeout(r, 120)); });
    expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1);

    await act(async () => { traiter(); await new Promise((r) => setTimeout(r, 120)); });
    expect(apiMocks.streamMessage).toHaveBeenCalledTimes(2);
  });
});
