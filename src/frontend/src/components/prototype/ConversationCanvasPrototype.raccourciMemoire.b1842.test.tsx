/**
 * B-1842 : ⌘M ferme la Mémoire par `setEmbeddedView(null)` seul.
 *
 * `collapseEmbeddedView` refuse la sortie si une saisie est en cours, puis
 * `goBack` quand le store est encore sur cette vue. Le raccourci sautait les
 * deux : un formulaire modifié était démonté, et `activeView` restait
 * `memory` pendant que l’écran retombait sur l’accueil. Rouvrir les Contacts
 * devenait alors un no-op (`setView` ignore une valeur identique).
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { _viderSaisiesEnCours, inscrireSaisieEnCours } from '../../lib/saisieEnCours';
import { runAction } from '../../lib/actionRegistry';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function vueAffichee(): string | null {
  return screen.getByTestId('conversation-canvas-prototype').getAttribute('data-embedded-view');
}

function raccourciMemoire() {
  // jsdom n'annonce pas une plateforme Mac : le hook prend Ctrl. Les deux
  // modificateurs couvrent le poste et le test.
  window.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'm', metaKey: true, ctrlKey: true, bubbles: true,
  }));
}

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  _viderSaisiesEnCours();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  useNavigationStore.setState({ activeView: null, history: [] } as never);
  usePersonalisationStore.setState({ skipDashboard: false });
  usePanelStore.setState({
    showSettings: false, showSaveCommand: false, showContactModal: false, showProjectModal: false,
    showBoardPanel: false, showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
    showConversationSidebar: false,
  } as never);
});

afterEach(() => {
  _clearEscapeHandlers();
  _viderSaisiesEnCours();
});

describe('B-1842 : le raccourci mémoire ferme comme le retour de la vue', () => {
  it('ferme la mémoire, aligne le store, et la même vue se rouvre', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('memory.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('memory'));

    await act(async () => { raccourciMemoire(); });

    await waitFor(() => expect(vueAffichee()).toBe('accueil'));
    expect(useNavigationStore.getState().activeView).toBeNull();

    await act(async () => { runAction('memory.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('memory'));
  });

  it('une saisie en cours retient le raccourci : la mémoire reste affichée', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('memory.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('memory'));

    const garde = vi.fn(() => true);
    inscrireSaisieEnCours(garde);
    await act(async () => { raccourciMemoire(); });

    expect(vueAffichee()).toBe('memory');
    expect(useNavigationStore.getState().activeView).toBe('memory');
    expect(garde).toHaveBeenCalled();
  });
});
