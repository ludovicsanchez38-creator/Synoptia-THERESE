/**
 * Une information affichée en permanence doit informer.
 *
 * Relevé le 27/08/2026 : l'en-tête de la carte de scénario affiche
 * « THÉRÈSE · maintenant ». Ce « maintenant » est écrit en dur — il ne
 * change jamais, ne se met jamais à jour, et ne dit donc rien. Il occupe
 * une place permanente à l'écran pour un contenu nul.
 *
 * La règle posée par la revue : on ne retire pas, on renseigne. Un horaire
 * réel a un usage — savoir de quand date ce qu'on lit — là où « maintenant »
 * n'en a aucun.
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

describe('L’en-tête de la carte dit une heure, pas « maintenant »', () => {
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

  it('affiche une heure lisible plutôt que le mot « maintenant »', async () => {
    await act(async () => {
      render(<ConversationCanvasPrototype />);
    });

    const entete = await waitFor(() => {
      const noeud = screen.getByText('THÉRÈSE', { selector: 'div' });
      expect(noeud).toBeInTheDocument();
      return noeud;
    });

    expect(entete.textContent).not.toContain('maintenant');
    // Une heure au format français : 9:05, 14:32…
    expect(entete.textContent).toMatch(/\d{1,2}[:h]\d{2}/);
  });
});
