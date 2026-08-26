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

describe('Revue Soso du hotfix - findings S1', () => {
  beforeEach(reinitialiser);

  it('S1-1 : aucun panneau ne se déclare modal, car le rail reste vivant', async () => {
    // Le rail et l'en-tête portent `data-dialog-allow` : ils restent
    // cliquables PAR CHOIX PRODUIT (navigation permanente). Un panneau qui
    // laisse une partie de l'écran interactive n'est donc jamais une modale
    // au sens ARIA - il isole seulement la zone qu'il RECOUVRE.
    poserLargeurEcran(false);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    const panneau = await waitFor(() => {
      const n = document.querySelector('[aria-labelledby="prototype-context-canvas-title"]');
      expect(n).toBeTruthy();
      return n as HTMLElement;
    });

    expect(panneau.getAttribute('aria-modal')).toBeNull();
    // Le rail reste atteignable : il n'est ni inerte ni masqué
    const porteDuTiroir = screen.getByRole('button', { name: 'Plus d’outils' });
    expect(porteDuTiroir.closest('[inert]')).toBeNull();
    // ...et la zone recouverte, elle, est bien isolée
    expect(screen.getByTestId('coque-colonne-principale').hasAttribute('inert')).toBe(true);
  });

  it('S1-3 : un panneau ne s’inscrit JAMAIS dans la pile des pièges', async () => {
    // Passe 2 (findings 1 et 2) : même en petit écran, piéger le clavier
    // rendait le rail et l'en-tête - présentés comme actifs - inatteignables
    // au clavier, et le réarmement au redimensionnement volait Escape à une
    // modale ouverte par-dessus. Un panneau ne pilote jamais le clavier.
    const { trapStackTaille } = await import('../../hooks/useDialogFocusTrap');
    poserLargeurEcran(false);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    await waitFor(() => {
      expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
    });

    expect(trapStackTaille()).toBe(0);
    // ...et le rail reste atteignable au clavier (aucun piège ne le boucle)
    const porteDuTiroir = screen.getByRole('button', { name: 'Plus d’outils' });
    porteDuTiroir.focus();
    expect(document.activeElement).toBe(porteDuTiroir);
  });
});

describe('Revue Soso du hotfix - S1-2 : pas de contrôle tabbable sous un panneau opaque', () => {
  it('les six panneaux latéraux passent côte à côte au seuil xl', async () => {
    const sources = await Promise.all(
      [
        'ImagesWorkspaceCanvas',
        'VoiceWorkspaceCanvas',
        'FollowUpsWorkspaceCanvas',
        'DeliverablesWorkspaceCanvas',
        'CalculatorWorkspaceCanvas',
      ].map(async (nom) => {
        const module = await import(`./${nom}.tsx?raw`);
        return [nom, module.default as string] as const;
      }),
    );

    const sansCoteACote = sources
      .filter(([, code]) => !code.includes('xl:relative'))
      .map(([nom]) => nom);
    expect(sansCoteACote).toEqual([]);
  });
});

describe('Revue Soso passe 3 - le redimensionnement ne vole pas le focus', () => {
  beforeEach(reinitialiser);

  it('quand le panneau devient couvrant, le focus quitte la zone isolée', async () => {
    // Passe 3 (F1) : franchir 1280 px réarmait tout le cycle de focus.
    // Passe 4 (F1) : la correction laissait le focus dans une zone devenue
    // `inert` - le champ paraissait actif mais la frappe se perdait. Le focus
    // doit SUIVRE : il entre dans le panneau, seule zone encore utilisable.
    const auditeurs: Array<() => void> = [];
    let coteACote = true;
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      // getter : le mock doit SUIVRE la largeur, pas la figer à la création
      get matches() {
        return query.includes('min-width: 1280px') ? coteACote : false;
      },
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: (_evt: string, cb: () => void) => auditeurs.push(cb),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;

    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    await waitFor(() => {
      expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
    });

    // L'utilisateur travaille dans le composeur
    const composeur = screen.getByPlaceholderText('Demande à Thérèse d’organiser, créer ou agir…');
    composeur.focus();
    expect(document.activeElement).toBe(composeur);

    // La fenêtre passe sous le seuil : le panneau devient couvrant
    await act(async () => {
      coteACote = false;
      auditeurs.forEach((cb) => cb());
    });

    const panneau = document.querySelector(
      '[aria-labelledby="prototype-context-canvas-title"]',
    ) as HTMLElement;
    expect(panneau.contains(document.activeElement)).toBe(true);
    expect(document.activeElement).not.toBe(composeur);
  });

  it('le focus ne reste jamais dans une zone isolée (passe 4, F1)', async () => {
    const auditeurs: Array<() => void> = [];
    let coteACote = true;
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      get matches() {
        return query.includes('min-width: 1280px') ? coteACote : false;
      },
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: (_evt: string, cb: () => void) => auditeurs.push(cb),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;

    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);
    await waitFor(() => {
      expect(document.querySelector('[aria-labelledby="prototype-context-canvas-title"]')).toBeTruthy();
    });

    screen.getByPlaceholderText('Demande à Thérèse d’organiser, créer ou agir…').focus();
    await act(async () => {
      coteACote = false;
      auditeurs.forEach((cb) => cb());
    });

    expect((document.activeElement as HTMLElement)?.closest('[inert]')).toBeNull();
  });
});

describe('Revue Soso passe 4 - ordre de nettoyage du focus', () => {
  it('P4-F2 : le déclencheur n’est plus isolé quand le focus lui revient', async () => {
    const { useDialogFocusTrap } = await import('../../hooks/useDialogFocusTrap');
    const { useRef } = await import('react');

    let isoleAuMomentDuFocus: boolean | null = null;

    function Modale({ ouverte }: { ouverte: boolean }) {
      const ref = useRef<HTMLDivElement>(null);
      useDialogFocusTrap(ref, { active: ouverte, isolateBackground: true });
      return ouverte ? (
        <div ref={ref} data-testid="modale">
          <button type="button">Dans la modale</button>
        </div>
      ) : null;
    }

    function Page({ ouverte }: { ouverte: boolean }) {
      return (
        <div>
          <button type="button" data-testid="declencheur">Ouvrir</button>
          <Modale ouverte={ouverte} />
        </div>
      );
    }

    const { rerender } = render(<Page ouverte={false} />);
    const declencheur = screen.getByTestId('declencheur');
    declencheur.focus();
    // On observe l'état d'isolation AU MOMENT où le focus lui est rendu :
    // dans un vrai navigateur, focus() sur un élément `inert` est ignoré.
    declencheur.focus = () => {
      isoleAuMomentDuFocus = declencheur.closest('[inert]') !== null;
    };

    rerender(<Page ouverte />);
    await waitFor(() => expect(screen.getByTestId('modale')).toBeInTheDocument());
    rerender(<Page ouverte={false} />);

    expect(isoleAuMomentDuFocus).toBe(false);
  });
});
