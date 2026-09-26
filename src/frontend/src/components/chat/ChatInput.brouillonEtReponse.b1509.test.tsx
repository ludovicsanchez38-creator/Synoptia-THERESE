/**
 * B-1509 et B-1510 (R-125-1 et R-125-2, V3 de P-125) : le brouillon est
 * effacé au moment où son texte quitte le champ, jamais à la fin d'une
 * réponse ; un échec ne réécrit pas le brouillon avec le message raté.
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

function fluxControle(echec = false) {
  let liberer!: () => void;
  const fin = new Promise<void>((resolve) => { liberer = resolve; });
  apiMocks.streamMessage.mockReturnValue((async function* () {
    yield { type: 'text', content: 'Réponse' };
    await fin;
    if (echec) throw new Error('Fournisseur injoignable');
    yield { type: 'done' };
  })());
  return () => liberer();
}

describe('ChatInput - brouillon et réponse en cours', () => {
  let stockage: Record<string, string>;
  beforeEach(() => {
    vi.clearAllMocks();
    stockage = {};
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
      conversations: [conversation('orion', 'Orion'), conversation('veille', 'Veille')],
      currentConversationId: 'orion', isStreaming: false, queuedPrompt: null,
    } as never);
  });
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  async function envoyer(texte: string) {
    fireEvent.change(champ(), { target: { value: texte } });
    await act(async () => { fireEvent.click(screen.getByTestId('chat-send-btn')); });
  }

  it('B-1509 : un texte tapé pendant la réponse survit à la fin de celle-ci', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    const liberer = fluxControle();
    await envoyer('Premier message');
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    fireEvent.change(champ(), { target: { value: 'Idée pour la suite' } });
    act(() => { vi.advanceTimersByTime(6000); });
    expect(stockage['therese-draft-orion']).toBe('Idée pour la suite');

    await act(async () => { liberer(); });
    act(() => { vi.advanceTimersByTime(6000); });
    expect(stockage['therese-draft-orion']).toBe('Idée pour la suite');
  });

  it('B-1510 : un échec ne réécrit pas le brouillon avec le message raté', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    const liberer = fluxControle(true);
    await envoyer('Message qui va échouer');
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    fireEvent.change(champ(), { target: { value: 'Brouillon plus récent' } });
    act(() => { vi.advanceTimersByTime(6000); });

    await act(async () => { liberer(); });
    act(() => { vi.advanceTimersByTime(6000); });
    expect(stockage['therese-draft-orion']).toBe('Brouillon plus récent');
    expect(champ().value).toBe('Brouillon plus récent');
  });

  it('B-1510 : champ vide, le message raté revient au champ et au brouillon', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    const liberer = fluxControle(true);
    await envoyer('Message qui va échouer');
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });

    await act(async () => { liberer(); });
    act(() => { vi.advanceTimersByTime(6000); });
    expect(champ().value).toBe('Message qui va échouer');
    expect(stockage['therese-draft-orion']).toBe('Message qui va échouer');
  });

  it('B-1525 : une recherche approfondie lancée juste après la frappe ne revient pas en brouillon', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    apiMocks.streamDeepResearch.mockReturnValue((async function* () {
      yield { type: 'done', content: '' };
    })());
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    fireEvent.change(champ(), { target: { value: 'Marché des menuiseries en Provence' } });
    act(() => { vi.advanceTimersByTime(2000); });
    await act(async () => { fireEvent.click(screen.getByLabelText('Lancer une recherche approfondie')); });
    act(() => { vi.advanceTimersByTime(6000); });
    expect(stockage['therese-draft-orion']).toBeUndefined();
  });
});

