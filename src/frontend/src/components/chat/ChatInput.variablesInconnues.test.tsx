/**
 * B-634 (persona Sophie, c4) : « Utiliser » un prompt à variables affichait
 * « 0 variable résolue - inconnues : {nom_client}, … » dans un DIV inerte,
 * sans bouton, sans dire quoi faire, et l'envoi restait actif. La puce doit
 * dire que ces jetons sont à remplacer dans le message et offrir le geste :
 * sélectionner le premier jeton inconnu dans le composeur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('B-634 : les variables inconnues d’un prompt donnent le moyen de les combler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama',
      model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'],
      available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('la puce explique quoi faire et un bouton sélectionne le premier jeton à remplacer', async () => {
    render(<ChatInput />);
    const zone = (await screen.findByTestId('chat-message-input')) as HTMLTextAreaElement;
    fireEvent.change(zone, { target: { value: 'Bonjour {prenom}, relance {nom_client}' } });

    const puce = await screen.findByTestId('variables-preview-chip', {}, { timeout: 3000 });
    expect(puce).toHaveTextContent(/à remplacer dans le message avant l’envoi|à remplacer dans le message avant l'envoi/i);

    const bouton = await screen.findByRole('button', { name: /Compléter dans le message/ });
    fireEvent.click(bouton);

    await waitFor(() => expect(document.activeElement).toBe(zone));
    const debut = 'Bonjour '.length;
    expect(zone.selectionStart).toBe(debut);
    expect(zone.selectionEnd).toBe(debut + '{prenom}'.length);
  });
});
