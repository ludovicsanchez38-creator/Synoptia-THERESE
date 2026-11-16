/**
 * B-1843 : depuis une vue, la palette ouvre un parcours sans aligner le store.
 *
 * `chooseScenario` posait `embeddedView` à null et ne faisait `goBack` que si
 * la vue active était le chat. L’écran montrait le parcours, `activeView`
 * restait l’ancienne vue, et `setView` de la même valeur ne la rouvrait plus.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { runAction } from '../../lib/actionRegistry';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function vueAffichee(): string | null {
  return screen.getByTestId('conversation-canvas-prototype').getAttribute('data-embedded-view');
}

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
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

describe('B-1843 : un parcours choisi depuis une vue laisse le store sur l’accueil', () => {
  it('Écrire depuis l’agenda affiche le parcours et l’agenda se rouvre ensuite', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('calendar.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('calendar'));

    fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
    const palette = screen.getByRole('dialog', { name: 'Rechercher une commande, une capacité ou une donnée' });
    fireEvent.click(within(palette).getByRole('option', { name: /Écrire un e-mail/ }));

    await waitFor(() => expect(vueAffichee()).toBe('accueil'));
    expect(screen.getByText('Nouveau message')).toBeInTheDocument();
    expect(useNavigationStore.getState().activeView).toBeNull();

    await act(async () => { runAction('calendar.open'); });
    await waitFor(() => expect(vueAffichee()).toBe('calendar'));
  });
});
