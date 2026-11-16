import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { usePanelStore } from '../../stores/panelStore';
import { grantCloudConsent, hasCloudConsent } from '../../lib/consent';
import { runNavigationAction } from '../../lib/clientActions';
import { ChatInput } from './ChatInput';

const api = vi.hoisted(() => ({
  getLLMConfig: vi.fn(), setLLMConfig: vi.fn(), streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(), indexFile: vi.fn(),
}));
const attente = vi.hoisted(() => ({
  attendrePersistance: vi.fn(), assurerConversationPersistee: vi.fn(),
}));
const variables = vi.hoisted(() => ({ previewVariables: vi.fn() }));
const tauri = vi.hoisted(() => ({
  listeners: new Map<string, (event: { payload: { paths: string[] } }) => void>(),
}));
vi.mock('@tauri-apps/api/event', () => ({
  listen: async (name: string, handler: (event: { payload: { paths: string[] } }) => void) => {
    tauri.listeners.set(name, handler);
    return () => { tauri.listeners.delete(name); };
  },
  emit: vi.fn(),
}));
vi.mock('../../services/api', () => ({ ...api, ApiError: class extends Error {} }));
vi.mock('../../lib/rattachementConversation', () => attente);
vi.mock('../../services/api/variables', async original => ({
  ...(await original<typeof import('../../services/api/variables')>()), ...variables,
}));
vi.mock('../../lib/consent', async original => ({
  ...(await original<typeof import('../../lib/consent')>()),
  grantCloudConsent: vi.fn(), hasCloudConsent: vi.fn(),
}));
vi.mock('../../lib/clientActions', async original => ({
  ...(await original<typeof import('../../lib/clientActions')>()), runNavigationAction: vi.fn(),
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

function differe<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(r => { resolve = r; });
  return { promise, resolve };
}
const apercu = (resolved: string) => ({ resolved, unknown: [], errors: [], variables_revision: 'r1' });

beforeEach(() => {
  vi.clearAllMocks();
  installLocalStorageStub();
  useStatusStore.setState({ connectionState: 'connected', notifications: [] });
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
  attente.attendrePersistance.mockResolvedValue(undefined);
  attente.assurerConversationPersistee.mockImplementation(async (id: string) => id);
  variables.previewVariables.mockImplementation(async (text: string) => apercu(text));
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); tauri.listeners.clear(); });

type Parcours = 'message' | 'recherche';
async function composer(message = 'Demande fictive A') {
  localStorage.setItem('therese-draft-B', message);
  render(<ChatInput />);
  const champ = screen.getByRole('textbox', { name: 'Message à THÉRÈSE' });
  fireEvent.change(champ, { target: { value: message } });
  await waitFor(() => expect(screen.getByTestId('chat-send-btn')).toBeEnabled());
  return champ;
}
function envoyer(parcours: Parcours = 'message') {
  fireEvent.click(parcours === 'recherche'
    ? screen.getByRole('button', { name: 'Lancer une recherche approfondie' })
    : screen.getByTestId('chat-send-btn'));
}
async function proposer(parcours: Parcours = 'message', message?: string) {
  const champ = await composer(message);
  envoyer(parcours);
  await screen.findByTestId('chat-cloud-consent');
  return champ;
}
function autoriser() { fireEvent.click(screen.getByRole('button', { name: 'Autoriser et envoyer' })); }
function basculer() { act(() => useChatStore.getState().loadConversation('B')); }
async function terminer<T>(suspension: ReturnType<typeof differe<T>>, valeur: T) {
  await act(async () => { suspension.resolve(valeur); await new Promise(r => setTimeout(r, 10)); });
}

async function composerAvecImage() {
  vi.stubGlobal('__TAURI__', {});
  const champ = await composer();
  await waitFor(() => expect(tauri.listeners.has('tauri://drag-drop')).toBe(true));
  deposer('A.png');
  expect(screen.getByRole('button', { name: 'Retirer A.png' })).toBeInTheDocument();
  return champ;
}
function deposer(path: string) {
  act(() => tauri.listeners.get('tauri://drag-drop')?.({ payload: { paths: [path] } }));
}

it('R2.3 : le vrai dépôt Tauri ignore B.png pendant l’accord pour A.png', async () => {
  await composerAvecImage();
  envoyer();
  await screen.findByTestId('chat-cloud-consent');
  deposer('B.png');
  autoriser();
  await waitFor(() => expect(api.streamMessage).toHaveBeenCalledTimes(1));
  expect(api.streamMessage.mock.calls[0][0].file_paths).toEqual(['A.png']);
});

it('R2.3 : le retrait d’une pièce jointe invalide l’accord affiché', async () => {
  const champ = await composerAvecImage();
  const retirer = screen.getByRole('button', { name: 'Retirer A.png' });
  envoyer();
  await screen.findByTestId('chat-cloud-consent');
  // Simule une mise à jour externe malgré l'isolation DOM du composeur.
  fireEvent.click(retirer);
  autoriser();
  expect(grantCloudConsent).not.toHaveBeenCalled();
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(champ).toHaveValue('Demande fictive A');
});

it('R2.3 : refuse le remplacement de A.png par B.png après le clic, à finalité égale', async () => {
  const champ = await composerAvecImage();
  const retirer = screen.getByRole('button', { name: 'Retirer A.png' });
  envoyer();
  await screen.findByTestId('chat-cloud-consent');
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  autoriser();
  fireEvent.click(retirer);
  deposer('B.png');
  await act(async () => { await vi.advanceTimersByTimeAsync(1); });
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(champ).toHaveValue('Demande fictive A');
});

it.each(['llm', 'documents'])('R2.3 : refuse une finalité différente après accord %s', async purpose => {
  const initial = purpose === 'documents' ? '/fichier A.txt' : 'Bonjour';
  variables.previewVariables.mockResolvedValue(apercu(initial));
  const champ = await proposer('message', '{demande}');
  variables.previewVariables.mockResolvedValue(apercu(purpose === 'documents' ? 'Bonjour' : '/fichier B.txt'));
  autoriser();
  await act(async () => { await new Promise(r => setTimeout(r, 10)); });
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(champ).toHaveValue('{demande}');
  expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
    expect.objectContaining({ title: 'Demande à confirmer à nouveau' }),
  ]));
});

it.each(['variables', 'persistance', 'recherche'] as const)('R2.3 : revalide la destination pendant l’attente %s', async etape => {
  const message = etape === 'variables' ? 'Demande {client}' : 'Demande fictive A';
  const champ = await proposer(etape === 'recherche' ? 'recherche' : 'message', message);
  const suspension = differe<ReturnType<typeof apercu>>();
  const operation = etape === 'variables' ? variables.previewVariables : attente.attendrePersistance;
  const appelsAvant = operation.mock.calls.length;
  operation.mockReturnValue(suspension.promise);
  autoriser();
  await waitFor(() => expect(operation.mock.calls.length).toBeGreaterThan(appelsAvant));
  api.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'autre', available_models: ['autre'], available: true });
  await act(async () => { window.dispatchEvent(new Event('therese:llm-config-changed')); });
  await terminer(suspension, apercu(message));
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(api.streamDeepResearch).not.toHaveBeenCalled();
  expect(champ).toHaveValue(message);
});

it.each(['message', 'recherche'] as const)('R2.2 : Tab dans l’accord ne choisit pas une commande slash (%s)', async parcours => {
  const champ = await proposer(parcours, '/');
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  fireEvent.keyDown(annuler, { key: 'Tab' });
  expect(runNavigationAction).not.toHaveBeenCalled();
  expect(screen.queryByText('Commandes disponibles')).not.toBeInTheDocument();
  expect(champ).toHaveValue('/');
  fireEvent.keyDown(annuler, { key: 'Escape' });
  expect(champ).toHaveValue('/');
  expect(api.streamMessage).not.toHaveBeenCalled();
});

it.each(['premier envoi', 'reprise après accord'])('R2.1 : garde la conversation pendant previewVariables (%s)', async phase => {
  const message = 'Demande {client}';
  const champ = phase === 'premier envoi' ? await composer(message) : await proposer('message', message);
  const suspension = differe<ReturnType<typeof apercu>>();
  variables.previewVariables.mockReturnValue(suspension.promise);
  const appelsAvant = variables.previewVariables.mock.calls.length;
  if (phase === 'premier envoi') envoyer();
  else autoriser();
  await waitFor(() => expect(variables.previewVariables.mock.calls.length).toBeGreaterThan(appelsAvant));
  basculer();
  await terminer(suspension, apercu(message));
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(screen.queryByTestId('chat-cloud-consent')).not.toBeInTheDocument();
  expect(champ).toHaveValue(message);
  expect(localStorage.getItem('therese-draft-B')).toBe(message);
});

const attentes = (['message', 'recherche'] as const).flatMap(parcours =>
  (['attendrePersistance', 'assurerConversationPersistee'] as const).map(etape => ({ parcours, etape })));
it.each(attentes)('R2.1 : garde la conversation pendant $etape ($parcours)', async ({ parcours, etape }) => {
  const champ = await proposer(parcours);
  const suspension = differe<string>();
  attente[etape].mockReturnValue(suspension.promise);
  autoriser();
  await waitFor(() => expect(attente[etape]).toHaveBeenCalledTimes(1));
  basculer();
  await terminer(suspension, 'A');
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(api.streamDeepResearch).not.toHaveBeenCalled();
  expect(useChatStore.getState().currentConversation()?.messages).toHaveLength(0);
  expect(champ).toHaveValue('Demande fictive A');
  expect(localStorage.getItem('therese-draft-B')).toBe('Demande fictive A');
});

it.each(['message', 'recherche'] as const)('R2.1 : préserve B quand le premier événement arrive après la bascule (%s)', async parcours => {
  const champ = await proposer(parcours);
  const suspension = differe<void>();
  const flux = parcours === 'message' ? api.streamMessage : api.streamDeepResearch;
  flux.mockImplementation(async function* () {
    await suspension.promise;
    yield { type: 'text', content: 'Réponse pour A', conversation_id: 'A' };
  });
  autoriser();
  await waitFor(() => expect(flux).toHaveBeenCalledTimes(1));
  // Le brouillon reste présent jusqu'à l'acquittement, aussi en recherche.
  expect(champ).toHaveValue('Demande fictive A');
  basculer();
  await terminer(suspension, undefined);
  expect(useChatStore.getState().currentConversation()?.messages).toHaveLength(0);
  expect(champ).toHaveValue('Demande fictive A');
  expect(localStorage.getItem('therese-draft-B')).toBe('Demande fictive A');
  expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
    expect.objectContaining({ title: 'Demande à confirmer à nouveau' }),
  ]));
});

it.each(['message', 'recherche'] as const)('R2.5 : conserve l’accord après adoption serveur (%s)', async parcours => {
  const champ = await proposer(parcours);
  act(() => useChatStore.getState().updateConversationId('A', 'serveur-A'));
  autoriser();
  await waitFor(() => expect(grantCloudConsent).toHaveBeenCalledTimes(1));
  const flux = parcours === 'message' ? api.streamMessage : api.streamDeepResearch;
  await waitFor(() => expect(flux).toHaveBeenCalledTimes(1));
  expect(flux.mock.calls[0][0]).toMatchObject({ conversation_id: 'serveur-A' });
  expect(champ).toHaveValue('');
});

it('R2.5 : explique pourquoi une demande devenue périmée ne part pas', async () => {
  const champ = await proposer();
  basculer();
  autoriser();
  expect(grantCloudConsent).not.toHaveBeenCalled();
  expect(api.streamMessage).not.toHaveBeenCalled();
  expect(champ).toHaveValue('Demande fictive A');
  expect(useStatusStore.getState().notifications).toEqual(expect.arrayContaining([
    expect.objectContaining({ title: 'Demande à confirmer à nouveau' }),
  ]));
});

it('R2.5 : garde l’identité adoptée lors du rafraîchissement de la liste serveur', async () => {
  await proposer();
  act(() => {
    const chat = useChatStore.getState();
    chat.updateConversationId('A', 'serveur-A');
    chat.setConversations(chat.conversations.map(c => ({
      id: c.id === 'A' ? 'serveur-A' : c.id, title: c.title,
      messages: [], createdAt: c.createdAt, updatedAt: c.updatedAt, synced: true,
    })));
  });
  autoriser();
  await waitFor(() => expect(api.streamMessage).toHaveBeenCalledTimes(1));
  expect(api.streamMessage.mock.calls[0][0]).toMatchObject({ conversation_id: 'serveur-A' });
});
