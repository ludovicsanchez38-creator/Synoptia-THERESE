/**
 * Hotfix 0.48.1 - un panneau côte à côte n'est pas une modale.
 *
 * Bug signalé par Ludo (25/08) : ouvrir un panneau latéral (contexte de
 * scénario, vue embarquée, outil) rendait TOUTE la colonne principale
 * `inert` - plus un clic, plus un scroll, plus un focus. Cause : le focus
 * trap posait `isolateBackground` même quand le panneau est côte à côte.
 *
 * Règle : l'isolation ne vaut que quand le panneau COUVRE l'écran (petit
 * écran, sous le seuil xl de Tailwind). Dans ce cas seulement, un voile
 * grisé le dit visuellement - voile NON cliquable (BUG-156 : la fermeture
 * au clic sur le fond avait été refusée par les testeurs).
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { runAction } from '../../lib/actionRegistry';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

/** Simule la largeur d'écran vue par les media queries. */
function poserLargeurEcran(cotesACote: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('min-width: 1280px') ? cotesACote : false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
}

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

describe('Une vue embarquée ne bloque jamais la colonne principale', () => {
  beforeEach(() => {
    reinitialiser();
    poserLargeurEcran(true);
  });

  it('le rail et l’en-tête restent vivants quand Contacts est ouvert', async () => {
    // La vue embarquée REMPLACE la conversation ; ce qui doit rester
    // interactif, c'est tout ce qui l'entoure (rail, en-tête, recherche).
    render(<ConversationCanvasPrototype />);

    await act(async () => { runAction('memory.open'); });
    await screen.findByTestId('prototype-unified-view');

    expect(document.querySelectorAll('[inert]')).toHaveLength(0);
    const porteDuTiroir = screen.getByRole('button', { name: 'Plus d’outils' });
    expect(porteDuTiroir.closest('[inert]')).toBeNull();
    expect(porteDuTiroir.closest('[aria-hidden="true"]')).toBeNull();
  });

  it('la vue embarquée ne se déclare pas modale (Tab doit pouvoir en sortir)', async () => {
    render(<ConversationCanvasPrototype />);

    await act(async () => { runAction('memory.open'); });
    const vue = await screen.findByTestId('prototype-unified-view');

    expect(vue.getAttribute('aria-modal')).not.toBe('true');
  });
});

describe('Un panneau latéral n’isole que s’il couvre l’écran', () => {
  beforeEach(reinitialiser);

  it('grand écran : la colonne reste vivante et aucun voile ne s’affiche', async () => {
    poserLargeurEcran(true);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    await waitFor(() => {
      expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
    });

    const colonne = screen.getByTestId('coque-colonne-principale');
    expect(colonne.hasAttribute('inert')).toBe(false);
    expect(screen.queryByTestId('panneau-voile')).toBeNull();
  });

  it('petit écran : la colonne est isolée ET le voile grisé le dit', async () => {
    poserLargeurEcran(false);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    await waitFor(() => {
      expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
    });

    const colonne = screen.getByTestId('coque-colonne-principale');
    expect(colonne.hasAttribute('inert')).toBe(true);
    const voile = screen.getByTestId('panneau-voile');
    expect(voile).toBeInTheDocument();
    expect(voile.getAttribute('aria-hidden')).toBe('true');
  });

  it('le voile ne ferme pas le panneau au clic (BUG-156)', async () => {
    poserLargeurEcran(false);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    const voile = await screen.findByTestId('panneau-voile');

    fireEvent.click(voile);

    expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
  });
});
