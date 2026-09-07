/**
 * B-456 (cycle 4) : la commande « Conversations » et le geste local avaient
 * deux chemins qui ne se synchronisaient pas ; une commande pouvait rouvrir
 * (et changer de surface) un tiroir déjà ouvert.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { CLIENT_ACTION_EVENT } from '../../lib/clientActions';

function reinitialiser() {
  vi.clearAllMocks();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  usePanelStore.setState({
    showSettings: false, requestedSettingsTab: null, showSaveCommand: false,
    showContactModal: false, showProjectModal: false, showBoardPanel: false,
    showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
    showConversationSidebar: false,
  });
  _clearEscapeHandlers();
  useNavigationStore.setState({ activeView: 'chat', history: [] });
  usePersonalisationStore.setState({ skipDashboard: false });
}

describe('B-456 : un seul chemin pour le tiroir Conversations', () => {
  beforeEach(reinitialiser);

  function actionDeLaCoque(actionId: string) {
    // Le chemin de la palette et des boutons de la coque (runUnifiedAction),
    // distinct du registre d'actions qui bascule directement le store.
    window.dispatchEvent(new CustomEvent(CLIENT_ACTION_EVENT, { detail: { actionId } }));
  }

  it('la commande de la coque ouvre puis ferme le tiroir, et le store suit à chaque pas', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => { actionDeLaCoque('conversations.toggle'); });
    await waitFor(() => screen.getByTestId('prototype-conversation-drawer'));
    expect(usePanelStore.getState().showConversationSidebar).toBe(true);

    await act(async () => { actionDeLaCoque('conversations.toggle'); });
    await waitFor(() => expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeInTheDocument());
    expect(usePanelStore.getState().showConversationSidebar).toBe(false);
  });

  it('le registre d’actions (raccourci B) et la coque partagent le même état', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('conversations.toggle'); });
    await waitFor(() => screen.getByTestId('prototype-conversation-drawer'));
    await act(async () => { actionDeLaCoque('conversations.toggle'); });
    await waitFor(() => expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeInTheDocument());
    expect(usePanelStore.getState().showConversationSidebar).toBe(false);
  });

  it('un tiroir déjà ouvert n’est pas rouvert par la bascule du store', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('conversations.toggle'); });
    await waitFor(() => screen.getByTestId('prototype-conversation-drawer'));

    // Le store est déjà à vrai : une bascule externe le repasse à faux puis vrai.
    await act(async () => { usePanelStore.getState().toggleConversationSidebar(); });
    await waitFor(() => expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeInTheDocument());
    await act(async () => { usePanelStore.getState().toggleConversationSidebar(); });
    await waitFor(() => screen.getByTestId('prototype-conversation-drawer'));
    expect(usePanelStore.getState().showConversationSidebar).toBe(true);
  });
});
