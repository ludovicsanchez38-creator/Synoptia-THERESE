/**
 * Lot M1 : la puce du modèle dit « Préversion » pour Mistral Large 4,
 * et continue d'afficher l'effort choisi.
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

describe('puce du modèle, lot M1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('Mistral Large 4 se voit en préversion, et le réglage d’effort n’est pas appliqué', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'mistral',
      model: 'mistral-large-4',
      available_models: ['mistral-medium-3-5', 'mistral-large-4'],
      available: true,
      effort: 'high',
      effort_resolu: null,
    });
    render(<ChatInput />);
    const option = await screen.findByRole('option', { name: 'mistral-large-4 (préversion)' });
    expect(option).toHaveTextContent('mistral-large-4 (préversion)');
    const select = screen.getByRole('combobox', { name: 'Modèle de conversation' });
    const badge = screen.getByText('Préversion');
    expect(select).toHaveAttribute('aria-describedby', badge.id);
    expect(select).toHaveAccessibleDescription('Préversion');
    expect(screen.getByText('réglage non appliqué à ce modèle')).toBeInTheDocument();
    expect(screen.queryByText('effort élevé')).not.toBeInTheDocument();
  });

  it('affiche l’effort transmis, pas le réglage demandé', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'grok',
      model: 'grok-4.7',
      available_models: ['grok-4.7'],
      available: true,
      effort: 'max',
      effort_resolu: 'xhigh',
    });
    render(<ChatInput />);
    expect(await screen.findByText('effort très élevé')).toBeInTheDocument();
    expect(screen.queryByText('effort maximal')).not.toBeInTheDocument();
  });
});
