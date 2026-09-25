/**
 * B-1476 (recette P-146, lot 5, KO-3b) : Claude choisi sans clé. Le bandeau
 * disait « Aucun modèle actif ne peut répondre… démarre Ollama avec un modèle
 * local » alors qu'Ollama tournait avec deux modèles, sans nommer le service
 * choisi ni la cause (la clé manquante).
 */
import { render, screen } from '@testing-library/react';
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

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {
    status = 500;
  },
}));
vi.mock('../../services/api/variables', () => ({
  jetonsMalFormes: () => [],
  hasVariableTokens: (t: string) => /\{[a-z_]+\}/.test(t),
  compterVariables: (t: string) => (t.match(/\{[a-z_]+\}/g) ?? []).length,
  previewVariables: vi.fn().mockResolvedValue({
    resolved: '',
    unknown: ['nom_client', 'prenom'],
    errors: [],
    variables_revision: 'r1',
  }),
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

describe('B-1476 : le bandeau nomme le service choisi et sa cause', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('un service en ligne sans clé : nommé, clé manquante, sans conseil Ollama', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-fable-5', available_models: [], available: false });
    render(<ChatInput />);
    const bandeau = await screen.findByTestId('chat-model-unavailable');
    expect(bandeau).toHaveTextContent('Anthropic');
    expect(bandeau).toHaveTextContent(/clé/);
    expect(bandeau).not.toHaveTextContent(/démarre Ollama/);
  });

  it('Ollama choisi mais indisponible : le conseil Ollama reste', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: [], available: false });
    render(<ChatInput />);
    const bandeau = await screen.findByTestId('chat-model-unavailable');
    expect(bandeau).toHaveTextContent(/Ollama/);
  });
});
