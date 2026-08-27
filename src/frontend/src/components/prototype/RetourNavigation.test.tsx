/**
 * Le retour ramène à l'écran précédent. En UN geste.
 *
 * Défaut trouvé le 27/08/2026 pendant l'audit UX. La coque démarre sur son
 * accueil conversationnel natif, mais le store de navigation démarre, lui,
 * sur la vue embarquée `home` — l'ancien tableau de bord, que plus personne
 * n'affiche au lancement. Le code le sait : un commentaire de la coque
 * explique qu'on n'appelle PAS `initializeView` « qui poserait la vue 'home'
 * et écraserait l'accueil conversationnel natif ». Mais l'état initial du
 * store, lui, n'a jamais été corrigé.
 *
 * Conséquence : ouvrir une vue empile `home`. Le bouton « Retour » dépile
 * donc vers `home`, un écran où l'utilisateur n'est jamais allé, et il faut
 * un deuxième geste — parfois un troisième — pour revenir vraiment.
 *
 * La pile ne ment pas seulement à la fermeture : elle ment DÈS L'OUVERTURE.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

/** L'écran réellement affiché, tel que la coque le déclare. */
function ecranAffiche(): string | null {
  return document
    .querySelector('[data-testid="conversation-canvas-prototype"]')
    ?.getAttribute('data-embedded-view') ?? null;
}

describe('Le retour est déterministe', () => {
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
    // L'état par défaut du store, celui de la PRODUCTION au lancement.
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it('au lancement, la pile est vide et aucune vue n’est empilée', () => {
    render(<ConversationCanvasPrototype />);

    expect(ecranAffiche()).toBe('accueil');
    expect(useNavigationStore.getState().history).toEqual([]);
  });

  it('ouvrir une vue puis revenir ramène à l’accueil en UN seul geste', async () => {
    render(<ConversationCanvasPrototype />);
    expect(ecranAffiche()).toBe('accueil');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Espaces de travail' }));
    });
    await waitFor(() => expect(ecranAffiche()).toBe('projects'));

    const retour = await screen.findByRole('button', { name: /Revenir/i });
    await act(async () => {
      fireEvent.click(retour);
    });

    expect(ecranAffiche()).toBe('accueil');
  });

  it('l’historique reflète l’écran affiché, jamais un écran fantôme', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Espaces de travail' }));
    });
    await waitFor(() => expect(ecranAffiche()).toBe('projects'));

    // On vient de l'accueil : la pile ne doit contenir aucune VUE, puisque
    // aucune vue n'était ouverte avant.
    expect(useNavigationStore.getState().history).toEqual([]);
  });
});
