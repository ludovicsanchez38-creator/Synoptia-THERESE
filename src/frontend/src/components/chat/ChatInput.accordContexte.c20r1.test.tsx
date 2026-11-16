import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { usePanelStore } from '../../stores/panelStore';
import { grantCloudConsent, hasCloudConsent } from '../../lib/consent';
import { ChatInput } from './ChatInput';

const api = vi.hoisted(() => ({
  getLLMConfig: vi.fn(), setLLMConfig: vi.fn(), streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(), indexFile: vi.fn(),
}));
vi.mock('../../services/api', () => ({ ...api, ApiError: class extends Error {} }));
vi.mock('../../lib/consent', async (original) => ({
  ...(await original<typeof import('../../lib/consent')>()),
  grantCloudConsent: vi.fn(), hasCloudConsent: vi.fn(),
}));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

beforeEach(() => {
  vi.clearAllMocks();
  installLocalStorageStub();
  useStatusStore.setState({ connectionState: 'connected' });
  usePanelStore.setState({ showSettings: false });
  useChatStore.setState({
    conversations: ['A', 'B'].map(id => ({ id, title: id, messages: [], synced: true,
      createdAt: new Date(), updatedAt: new Date() })),
    currentConversationId: 'A', isStreaming: false, queuedPrompt: null,
  });
  api.getLLMConfig.mockResolvedValue({ provider: 'openai', model: 'factice', available_models: ['factice'], available: true });
  vi.mocked(hasCloudConsent).mockReturnValue(false);
  vi.mocked(grantCloudConsent).mockImplementation((purpose, provider, dataCategories) => {
    vi.mocked(hasCloudConsent).mockReturnValue(true);
    return { purpose, provider, dataCategories, timestamp: '2026-01-01T00:00:00Z' };
  });
  api.streamMessage.mockImplementation(async function* () { yield { type: 'done' }; });
  api.streamDeepResearch.mockImplementation(async function* () { yield { type: 'done' }; });
});
afterEach(() => { vi.useRealTimers(); });

type Parcours = 'message' | 'documents' | 'mémoire' | 'recherche';
async function proposer(parcours: Parcours) {
  const message = parcours === 'documents' ? '/fichier document-fictif.txt' : 'Demande fictive A';
  // Même texte dans B : le contrôle de conversation doit fonctionner à lui seul.
  localStorage.setItem('therese-draft-B', message);
  if (parcours === 'mémoire') {
    vi.mocked(hasCloudConsent).mockReturnValue(true);
    api.streamMessage.mockImplementationOnce(async function* () {
      yield { type: 'memory_consent_required', conversation_id: 'A', message_id: 'source-A',
        provider: 'openai', purpose: 'llm' };
    });
  }
  render(<ChatInput />);
  const champ = screen.getByRole('textbox', { name: 'Message à THÉRÈSE' });
  fireEvent.change(champ, { target: { value: message } });
  await waitFor(() => expect(screen.getByTestId('chat-send-btn')).toBeEnabled());
  fireEvent.click(parcours === 'recherche'
    ? screen.getByRole('button', { name: 'Lancer une recherche approfondie' })
    : screen.getByTestId('chat-send-btn'));
  await screen.findByTestId('chat-cloud-consent');
  await waitFor(() => expect(useChatStore.getState().isStreaming).toBe(false));
  return champ;
}

const cas = (['message', 'documents', 'mémoire', 'recherche'] as const).flatMap(parcours =>
  (['conversation', 'texte'] as const).flatMap(changement =>
    (['avant le clic', 'après le clic'] as const).map(moment => ({ parcours, changement, moment }))));

it.each(cas)('R1.1 : refuse un accord périmé ($parcours, $changement, $moment)', async ({ parcours, changement, moment }) => {
  const champ = await proposer(parcours);
  const autoriser = screen.getByRole('button', { name: 'Autoriser et envoyer' });
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  if (moment === 'après le clic') fireEvent.click(autoriser);
  if (changement === 'conversation') {
    act(() => useChatStore.getState().loadConversation('B'));
  } else {
    // Mise à jour de la saisie pendant l'attente (par exemple un prompt reçu).
    fireEvent.change(champ, { target: { value: 'Autre demande fictive' } });
  }
  if (moment === 'avant le clic') fireEvent.click(autoriser);
  await act(async () => { await vi.advanceTimersByTimeAsync(1); });

  expect(api.streamMessage).toHaveBeenCalledTimes(parcours === 'mémoire' ? 1 : 0);
  expect(api.streamDeepResearch).not.toHaveBeenCalled();
  if (moment === 'avant le clic') expect(grantCloudConsent).not.toHaveBeenCalled();
  expect(champ).toHaveValue(changement === 'texte' ? 'Autre demande fictive'
    : parcours === 'documents' ? '/fichier document-fictif.txt' : 'Demande fictive A');
});
