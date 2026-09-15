/**
 * B-816 (cycle 9) : au retour d'une vue embarquée (Agenda, Contacts, Email…),
 * le focus retombait sur body alors que les canevas, le panneau Travaux et
 * les Paramètres rendent le focus à leur déclencheur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

describe('Coque - B-816, le retour d’une vue embarquée rend le focus au déclencheur', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    usePanelStore.setState({
      showSettings: false, requestedSettingsTab: null, showSaveCommand: false, showContactModal: false,
      showProjectModal: false, showBoardPanel: false, showShortcuts: false, showPromptLibrary: false,
      showCommandPalette: false, showConversationSidebar: false,
    });
    _clearEscapeHandlers();
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('« Ouvrir Agenda » puis « Retour » : le focus revient sur « Ouvrir Agenda »', async () => {
    render(<ConversationCanvasPrototype />);
    const ouvrir = await screen.findByRole('button', { name: /^Ouvrir Agenda/ });
    ouvrir.focus();
    fireEvent.click(ouvrir);
    const retour = await screen.findByRole('button', { name: 'Revenir à la conversation unifiée' });
    fireEvent.click(retour);
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: /^Ouvrir Agenda/ })));
  });
});
