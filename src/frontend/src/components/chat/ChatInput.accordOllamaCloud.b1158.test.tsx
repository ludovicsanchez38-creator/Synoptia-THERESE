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

describe('B-1158 accord pour Ollama Cloud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
      queuedPrompt: null,
    });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('demande l’accord avant d’envoyer à un modèle « :cloud »', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'kimi-k2.6:cloud',
      available_models: ['kimi-k2.6:cloud'], available: true,
    });
    apiMocks.streamMessage.mockReturnValue((async function* () {
      yield { type: 'done' };
    })());
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: 'Résume ce dossier client' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));

    // Laisse partir l'envoi s'il n'est pas retenu par un accord.
    await new Promise((r) => setTimeout(r, 50));
    const etat = {
      accordAffiche: screen.queryByTestId('chat-cloud-consent') !== null,
      envoisPartis: apiMocks.streamMessage.mock.calls.length,
    };
    expect(etat).toEqual({ accordAffiche: true, envoisPartis: 0 });
  });

  it('n’en demande pas pour un modèle Ollama installé (témoin)', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'qwen3:8b', available_models: ['qwen3:8b'], available: true,
    });
    apiMocks.streamMessage.mockReturnValue((async function* () {
      yield { type: 'done' };
    })());
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: 'Résume ce dossier client' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId('chat-cloud-consent')).toBeNull();
  });

  it('nomme Ollama Cloud dans la demande d’accord', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gpt-oss:120b-cloud', available_models: ['gpt-oss:120b-cloud'], available: true,
    });
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: 'Résume ce dossier client' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));
    const accord = await screen.findByTestId('chat-cloud-consent');
    expect(accord).toHaveTextContent('Ollama Cloud');
  });

  it('la recherche approfondie passe par la même règle', async () => {
    const source = (await import('node:fs')).readFileSync(
      (await import('node:path')).join(__dirname, 'ChatInput.tsx'), 'utf-8',
    );
    const bloc = source.slice(source.indexOf('const handleDeepResearch'), source.indexOf('const handleDeepResearch') + 700);
    expect(bloc).toContain('fournisseurDAccord(');
  });
});
