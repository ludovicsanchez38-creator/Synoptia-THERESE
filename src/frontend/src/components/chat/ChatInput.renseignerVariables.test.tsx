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
  createVariable: vi.fn().mockResolvedValue({ name: 'prenom', kind: 'text', value: 'Marie', description: null, updated_at: '' }),
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
import { createVariable, previewVariables } from '../../services/api/variables';

describe('ChatInput : renseigner les variables (P-049)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previewVariables).mockResolvedValue({ resolved: '', unknown: ['nom_client', 'prenom'], errors: [], variables_revision: 'r1' });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'gemma4-tia:latest', available_models: ['gemma4-tia:latest'], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('le bouton ouvre le formulaire, l’enregistrement recalcule l’aperçu et le message garde ses jetons', async () => {
    render(<ChatInput />);
    const zone = (await screen.findByTestId('chat-message-input')) as HTMLTextAreaElement;
    fireEvent.change(zone, { target: { value: 'Bonjour {prenom}, relance {nom_client}' } });
    await screen.findByTestId('variables-preview-chip', {}, { timeout: 3000 });
    const appelsAvant = vi.mocked(previewVariables).mock.calls.length;

    fireEvent.click(screen.getByRole('button', { name: 'Renseigner les variables' }));
    const champ = await screen.findByLabelText('{prenom}');
    expect(screen.getByRole('button', { name: /Compléter dans le message/ })).toBeInTheDocument();
    fireEvent.change(champ, { target: { value: 'Marie' } });
    vi.mocked(previewVariables).mockResolvedValue({ resolved: '', unknown: ['nom_client'], errors: [], variables_revision: 'r2' });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme variables' }));
    await waitFor(() => expect(createVariable).toHaveBeenCalledWith('prenom', 'text', 'Marie'));
    await waitFor(() => expect(vi.mocked(previewVariables).mock.calls.length).toBeGreaterThan(appelsAvant));
    expect(zone.value).toBe('Bonjour {prenom}, relance {nom_client}');
    await waitFor(() => expect(screen.getByTestId('variables-preview-chip')).toHaveTextContent(/inconnue : \{nom_client\}/));
  });

  it('Échap dans le formulaire le ferme et rend le focus au composeur', async () => {
    render(<ChatInput />);
    const zone = (await screen.findByTestId('chat-message-input')) as HTMLTextAreaElement;
    fireEvent.change(zone, { target: { value: 'Bonjour {prenom}' } });
    await screen.findByTestId('variables-preview-chip', {}, { timeout: 3000 });
    fireEvent.click(screen.getByRole('button', { name: 'Renseigner les variables' }));
    const champ = await screen.findByLabelText('{prenom}');
    fireEvent.keyDown(champ, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByLabelText('{prenom}')).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(zone));
  });
});
