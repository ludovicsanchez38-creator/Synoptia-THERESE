/**
 * P-156 (recette P-146, lot 5, KO-3a ; acceptée par délégation le 25/09) :
 * l'effort de raisonnement choisi dans Paramètres n'apparaissait nulle part
 * dans la conversation. La puce du modèle, qui dit déjà le modèle et
 * « local » ou « cloud », dit aussi l'effort quand il n'est pas « Auto ».
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

describe('P-156 : la puce du modèle dit l’effort choisi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('effort élevé : la puce le dit', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: ['qwen3:8b'], available: true, effort: 'high' });
    render(<ChatInput />);
    expect(await screen.findByText('effort élevé')).toBeInTheDocument();
  });

  it('effort automatique : rien de plus', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: ['qwen3:8b'], available: true, effort: 'auto' });
    render(<ChatInput />);
    await screen.findByText('qwen3:8b');
    expect(screen.queryByText(/^effort /)).toBeNull();
  });
});
