/**
 * B-1395 (persona Zoé, cycle 13) : un flux coupé (rechargement, moteur
 * arrêté) écrivait l'exception brute du navigateur, « network error », comme
 * réponse de Thérèse. Le composeur passe désormais par messageDErreurDuFlux.
 */
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

describe('ChatInput - une coupure du flux se dit en français (B-1395)', () => {
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

  it('la bulle de Thérèse ne contient pas « network error »', async () => {
    apiMocks.streamMessage.mockImplementation(async function* () {
      yield { type: 'text', content: '', conversation_id: 'conv-1' };
      throw new TypeError('network error');
    });
    render(<ChatInput />);
    const champ = await screen.findByTestId('chat-message-input');
    fireEvent.change(champ, { target: { value: 'Zoé : réponds juste OK.' } });
    fireEvent.keyDown(champ, { key: 'Enter' });

    await waitFor(() => {
      const messages = useChatStore.getState().conversations[0]?.messages ?? [];
      const reponse = messages.find((m) => m.role === 'assistant');
      expect(reponse?.content ?? '').toMatch(/^Réponse interrompue/);
    });
    const messages = useChatStore.getState().conversations[0]?.messages ?? [];
    expect(messages.some((m) => m.content.includes('network error'))).toBe(false);
  });
});
