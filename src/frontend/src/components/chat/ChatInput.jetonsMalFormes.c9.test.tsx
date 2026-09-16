/**
 * P-061 (lot 0.74) : la puce des variables annonçait « 1 variable résolue »
 * et laissait partir {mauvais-nom} sans avertissement.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

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
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('ChatInput - P-061, un jeton mal formé est signalé', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('« {mauvais-nom} » sans variable valide : une puce le dit et rappelle la forme attendue', async () => {
    render(<ChatInput />);
    const zone = (await screen.findByTestId('chat-message-input')) as HTMLTextAreaElement;
    fireEvent.change(zone, { target: { value: 'Relance {mauvais-nom} pour {2eme sujet}' } });
    const puce = await screen.findByTestId('variables-mal-formees-chip');
    expect(puce).toHaveTextContent(/{mauvais-nom}/);
    expect(puce).toHaveTextContent(/{2eme sujet}/);
    expect(puce).toHaveTextContent(/lettres minuscules, chiffres et _/);
  });
});
