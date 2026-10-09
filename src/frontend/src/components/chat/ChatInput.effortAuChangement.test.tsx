/**
 * Changer de modèle met à jour la puce dès la réponse, sans attendre
 * un second chargement. Si ce chargement ne revient pas, l'ancien
 * effort ne doit pas rester affiché.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';

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

describe('la puce suit le changement de modèle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('affiche l’effort de la réponse même si le rechargement ne revient pas', async () => {
    apiMocks.getLLMConfig.mockResolvedValueOnce({
      provider: 'grok',
      model: 'grok-4.6',
      available_models: ['grok-4.6', 'grok-4.7'],
      available: true,
      effort: 'high',
      effort_resolu: 'high',
    });
    apiMocks.getLLMConfig.mockImplementation(() => new Promise(() => {}));
    apiMocks.setLLMConfig.mockResolvedValue({
      provider: 'grok',
      model: 'grok-4.7',
      available_models: ['grok-4.6', 'grok-4.7'],
      available: true,
      effort: 'high',
      effort_resolu: 'xhigh',
    });

    render(<ChatInput />);
    expect(await screen.findByText('effort élevé')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Modèle de conversation'), {
      target: { value: 'grok-4.7' },
    });
    expect(await screen.findByText('effort très élevé')).toBeInTheDocument();
    expect(screen.queryByText('effort élevé')).not.toBeInTheDocument();
  });
});
