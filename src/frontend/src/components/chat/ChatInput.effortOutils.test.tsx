/**
 * La puce ne doit pas dire qu'un effort part quand les outils le retirent.
 * Chat Completions (gpt-6-sol) pose none. Responses (gpt-6.1-sol) le garde.
 */
import { render, screen } from '@testing-library/react';
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

function config(model: string, effortResolu: string) {
  return {
    provider: 'openai',
    model,
    available_models: [model],
    available: true,
    effort: 'high',
    effort_resolu: effortResolu,
  };
}

describe('puce d’effort et outils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('gpt-6-sol avec outils ne prétend pas envoyer l’effort', async () => {
    apiMocks.getLLMConfig.mockResolvedValue(config('gpt-6-sol', 'high'));
    render(<ChatInput />);
    const puce = await screen.findByText('effort désactivé avec les outils');
    expect(puce).toHaveAttribute(
      'title',
      'Les outils de la conversation désactivent l’effort pour ce modèle.',
    );
    expect(screen.queryByText('effort élevé')).not.toBeInTheDocument();
  });

  it('gpt-6.1-sol garde l’effort : les outils passent par Responses', async () => {
    apiMocks.getLLMConfig.mockResolvedValue(config('gpt-6.1-sol', 'xhigh'));
    render(<ChatInput />);
    expect(await screen.findByText('effort très élevé')).toBeInTheDocument();
    expect(screen.queryByText('effort désactivé avec les outils')).not.toBeInTheDocument();
  });
});
