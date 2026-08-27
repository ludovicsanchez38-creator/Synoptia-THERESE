/**
 * Une commande annoncée doit produire son effet.
 *
 * Trouvé le 27/08/2026 pendant l'audit UX. L'action « Conversations »
 * (raccourci B, visible dans la palette ⌘K) appelle
 * `toggleConversationSidebar` du panelStore — un drapeau que la coque
 * n'observe pas : elle a son propre tiroir en état local. La commande
 * bascule donc un booléen que personne n'affiche.
 *
 * C'est le pire cas d'une interface : un geste annoncé, exécuté sans
 * erreur, et sans le moindre effet visible. L'utilisateur croit avoir mal
 * cliqué.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

describe('Les commandes annoncées produisent leur effet', () => {
  beforeEach(() => {
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
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('« Conversations » ouvre réellement le tiroir des conversations', async () => {
    const { runAction } = await import('../../lib/actionRegistry');
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      expect(runAction('conversations.toggle')).toBe(true);
    });

    await waitFor(() =>
      expect(screen.getByTestId('prototype-conversation-drawer')).toBeInTheDocument(),
    );
  });

  it('un second appel le referme', async () => {
    const { runAction } = await import('../../lib/actionRegistry');
    render(<ConversationCanvasPrototype />);

    await act(async () => { runAction('conversations.toggle'); });
    await waitFor(() =>
      expect(screen.getByTestId('prototype-conversation-drawer')).toBeInTheDocument(),
    );

    await act(async () => { runAction('conversations.toggle'); });

    await waitFor(() =>
      expect(screen.queryByTestId('prototype-conversation-drawer')).toBeNull(),
    );
  });
});
