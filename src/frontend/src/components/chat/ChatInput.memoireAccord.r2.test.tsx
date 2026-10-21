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


import { grantCloudConsent, hasCloudConsent, MEMORY_CARDS_CATEGORY } from '../../lib/consent';

describe('R2 : accord mémoire sur le payload effectif', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const stockage = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => stockage.get(k) ?? null,
      setItem: (k: string, v: string) => stockage.set(k, v),
      removeItem: (k: string) => stockage.delete(k),
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [{ id: 'conv-serveur', title: 'Conversation', messages: [],
      createdAt: new Date(), updatedAt: new Date(), synced: true }],
      currentConversationId: 'conv-serveur', isStreaming: false, queuedPrompt: null });
    usePanelStore.setState({ showSettings: false });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'openai', model: 'factice', available_models: ['factice'], available: true });
    grantCloudConsent('llm', 'openai', ['message saisi']);
  });

  it('un ancien accord ne provoque aucune nouvelle question quand aucune fiche ne part', async () => {
    apiMocks.streamMessage.mockImplementation(() => (async function* () {
      yield { type: 'text', conversation_id: 'conv-serveur', content: 'Réponse factice.' };
      yield { type: 'done', conversation_id: 'conv-serveur' };
    })());
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: 'Bonjour' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId('chat-cloud-consent')).toBeNull();
  });

  it('le signal serveur demande l’accord puis reprend la même source sans doublon utilisateur', async () => {
    let appels = 0;
    apiMocks.streamMessage.mockImplementation(() => (async function* () {
      appels++;
      if (appels === 1) yield { type: 'memory_consent_required', conversation_id: 'conv-serveur', message_id: 'source-serveur',
        provider: 'openai', purpose: 'llm', content: 'Accord requis.' };
      else { yield { type: 'text', conversation_id: 'conv-serveur', content: 'Réponse factice.' };
        yield { type: 'done', conversation_id: 'conv-serveur' }; }
    })());
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    fireEvent.change(input, { target: { value: 'Aide-moi à rédiger.' } });
    fireEvent.click(screen.getByTestId('chat-send-btn'));
    const accord = await screen.findByTestId('chat-cloud-consent');
    expect(accord).toHaveTextContent('tes fiches mémoire');
    expect(accord).not.toHaveTextContent(MEMORY_CARDS_CATEGORY);
    expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser et envoyer' }));
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(2));
    expect(apiMocks.streamMessage.mock.calls[1][0]).toMatchObject({ resume_message_id: 'source-serveur', memory_card_grants: ['llm:openai'] });
    expect(hasCloudConsent('llm', 'openai', [MEMORY_CARDS_CATEGORY])).toBe(true);
    expect(useChatStore.getState().currentConversation()?.messages.filter(m => m.role === 'user')).toHaveLength(1);
  });
});

it('R2 : permet de choisir explicitement un échange sans fiches', async () => {
  vi.clearAllMocks();
  useStatusStore.setState({ connectionState: 'connected' });
  useChatStore.setState({ conversations: [{ id: 'conv-serveur', title: 'Conversation', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: true }], currentConversationId: 'conv-serveur', isStreaming: false, queuedPrompt: null });
  apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'factice', available_models: ['factice'], available: true });
  apiMocks.streamMessage.mockImplementation(() => (async function* () {
    yield { type: 'done', conversation_id: 'conv-serveur' };
  })());
  render(<ChatInput />);
  const input = await screen.findByPlaceholderText(PLACEHOLDER_COMPOSEUR);
  await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
  const option = screen.getByRole('checkbox', { name: 'Utiliser les fiches mémoire' });
  expect(option).toBeChecked();
  fireEvent.click(option);
  fireEvent.change(input, { target: { value: 'Sans mes fiches cette fois.' } });
  fireEvent.click(screen.getByTestId('chat-send-btn'));
  await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
  expect(apiMocks.streamMessage.mock.calls[0][0]).toMatchObject({ include_memory: false });
});
