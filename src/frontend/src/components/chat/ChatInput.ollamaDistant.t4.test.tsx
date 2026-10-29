/**
 * B-1158 (cycle 13) : aucun accord n'était demandé pour un modèle Ollama
 * Cloud, dont les requêtes partent chez ollama.com : le composeur testait le
 * fournisseur (« ollama » = local), pas le modèle. L'accord porte désormais
 * sur la destination réelle, sous la clé « ollama-cloud ».
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PLACEHOLDER_COMPOSEUR } from '../../lib/etabli';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' }),
}));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {
    status = 500;
  },
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({
  SlashCommandsMenu: () => null,
  detectSlashCommand: () => false,
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { installLocalStorageStub } from '../../test/localStorage-stub';
import { hasCloudConsent } from '../../lib/consent';

beforeEach(() => {
  vi.clearAllMocks();
  installLocalStorageStub();
  useStatusStore.setState({ connectionState: 'connected' });
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false, queuedPrompt: null });
  usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
  useAccessibilityStore.setState({ showKeyboardHints: true });
});

describe('accord pour le serveur Ollama distant classé par le moteur', () => {
  it.each([false, true])('nomme le serveur et attend l’accord (document : %s)', async (document) => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'llama3', available_models: ['llama3'], available: true,
      consent_provider: 'ollama-cloud', consent_label: 'Serveur Ollama distant (http://192.0.2.10:11434)',
    });
    apiMocks.streamMessage.mockImplementation(async function* () { yield { type: 'done' }; });
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: document ? '/analyse document-fictif.txt' : 'Bonjour' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));
    const accord = await screen.findByTestId('chat-cloud-consent');
    expect(accord).toHaveTextContent('Serveur Ollama distant (http://192.0.2.10:11434)');
    if (document) expect(accord).toHaveTextContent('documents');
    expect(apiMocks.streamMessage).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser et envoyer' }));
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
    expect(hasCloudConsent(document ? 'documents' : 'llm', 'ollama-cloud')).toBe(true);
  });
});
