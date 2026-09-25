/**
 * Variables (décision du 25/09, délégation de Ludo) : la puce comptait les
 * variables résolues sans montrer le message qui partirait. Elle montre le
 * message final, tel que le moteur l'a résolu.
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
    resolved: 'Bonjour Julien, voici le devis de la table en chêne.',
    unknown: [],
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

describe('Variables : l’aperçu du message final', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: ['qwen3:8b'], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('la puce montre le message tel qu’il partira', async () => {
    render(<ChatInput />);
    const champ = await screen.findByTestId('chat-message-input');
    fireEvent.change(champ, { target: { value: 'Bonjour {prenom}, voici le devis de la table en chêne.' } });
    const apercu = await screen.findByTestId('variables-message-final');
    expect(apercu).toHaveTextContent('Bonjour Julien, voici le devis de la table en chêne.');
  });
});
