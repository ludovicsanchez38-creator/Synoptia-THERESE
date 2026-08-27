/**
 * Cliquer une carte du tiroir ouvre ce qu'elle annonce.
 *
 * Avant : le clic posait une phrase dans le composeur et affichait un
 * bandeau « Capacité : X ». La destination — pourtant déclarée dans la
 * carte — n'était ouverte qu'au moment de VALIDER le composeur. Pour une
 * carte « Tâches », il fallait donc cliquer, puis comprendre qu'il restait
 * à appuyer sur Entrée. Un clic de trop, sur toutes les cartes qui mènent
 * simplement quelque part.
 *
 * La frontière posée par la revue : l'ouverture directe ne vaut que pour
 * une navigation SANS effet externe. Les cartes de type `prompt` gardent
 * leur prévisualisation — le texte doit rester éditable et non envoyé,
 * c'est une fonctionnalité et non un frottement.
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

function ecranAffiche(): string | null {
  return document
    .querySelector('[data-testid="conversation-canvas-prototype"]')
    ?.getAttribute('data-embedded-view') ?? null;
}

async function ouvrirLeTiroir() {
  render(<ConversationCanvasPrototype />);
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Plus d’outils' }));
  });
  await screen.findByRole('heading', { name: 'Ce que Thérèse sait mobiliser' });
}

describe('Une carte ouvre sa destination', () => {
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

  it('une carte qui mène à une vue l’ouvre au clic, sans second geste', async () => {
    await ouvrirLeTiroir();

    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /Tâches/ })[0]);
    });

    await waitFor(() => expect(ecranAffiche()).toBe('tasks'));
  });

  it('une carte qui ouvre un panneau l’ouvre aussi directement', async () => {
    await ouvrirLeTiroir();

    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /Relances et alertes/ })[0]);
    });

    await waitFor(() =>
      expect(screen.getByTestId('follow-ups-workspace-canvas')).toBeInTheDocument(),
    );
  });

  it('une carte de type « prompt » garde sa prévisualisation éditable', async () => {
    await ouvrirLeTiroir();
    // La recherche du tiroir traverse les groupes : plus robuste que de
    // dépendre de l'onglet ouvert par défaut.
    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText(/Chercher une capacité/), {
        target: { value: 'Recherche web' },
      });
    });
    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: /Recherche web/ })[0]);
    });

    // Le texte est proposé, pas envoyé : il attend une relecture.
    const composeur = await screen.findByPlaceholderText(/Demande à Thérèse/);
    expect((composeur as HTMLTextAreaElement).value.length).toBeGreaterThan(0);
    expect(useChatStore.getState().isStreaming).toBe(false);
  });
});
