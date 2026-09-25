/**
 * B-1370 (persona Hugo, cycle 13) : ouvrir une conversation depuis le tiroir
 * alors qu'un écran (Projets) était affiché laissait le focus sur « Projets »
 * du rail, ou sur la page : douze tabulations jusqu'au champ de message. Le
 * tiroir et l'écran rendaient chacun le focus à leur déclencheur en se
 * fermant ; choisir une conversation le pose désormais dans le champ.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));
vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  // Un modèle disponible : sans lui, le champ reste désactivé (vérification).
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'ollama', model: 'x', available_models: ['x'], available: true }),
}));

function rail(nom: string) {
  return screen.getByRole('navigation', { name: 'Navigation principale' }).querySelector<HTMLButtonElement>(`button[aria-label="${nom}"]`)!;
}

describe('B-1370 : choisir une conversation pose le focus dans le champ de message', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePanelStore.setState({ showConversationSidebar: false });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [{
        id: 'conv-orion', title: 'API client Orion', messages: [], messageCount: 2,
        createdAt: new Date(), updatedAt: new Date(), synced: true,
      }] as never,
      currentConversationId: null,
      isStreaming: false,
    });
  });

  it.each([
    ['depuis l’Accueil', null],
    ['depuis Projets', 'Projets'],
  ])('%s', async (_cas, ecran) => {
    render(<ConversationCanvasPrototype />);
    if (ecran) {
      await act(async () => { fireEvent.click(rail(ecran)); });
      await screen.findByRole('heading', { name: ecran });
    }
    await act(async () => { fireEvent.click(rail('Conversations')); });
    const choix = await screen.findByText('API client Orion');

    await act(async () => { fireEvent.click(choix); });

    const champ = await screen.findByTestId('chat-message-input');
    await waitFor(() => expect(document.activeElement).toBe(champ));
    // Le focus ne repart pas après les sorties animées.
    await act(async () => { await new Promise((r) => setTimeout(r, 400)); });
    expect(document.activeElement).toBe(champ);
  });

  it('P-124 : « Nouvelle conversation » du rail pose le focus dans le champ', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { fireEvent.click(rail('Projets')); });
    await screen.findByRole('heading', { name: 'Projets' });

    await act(async () => { fireEvent.click(rail('Nouvelle conversation')); });

    const champ = await screen.findByTestId('chat-message-input');
    await waitFor(() => expect(document.activeElement).toBe(champ));
  });

  it('P-124 : ⌘N pose aussi le focus dans le champ', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => { fireEvent.keyDown(window, { key: 'n', ctrlKey: true, metaKey: true }); });

    const champ = await screen.findByTestId('chat-message-input');
    await waitFor(() => expect(document.activeElement).toBe(champ));
  });
});
