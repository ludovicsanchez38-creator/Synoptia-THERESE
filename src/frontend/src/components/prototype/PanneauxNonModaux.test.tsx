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
  it('les cinq canevas de travail passent côte à côte au seuil xl', async () => {
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

  /**
   * Le SIXIÈME panneau — le canevas de contexte — vit dans
   * `ConversationCanvasPrototype.tsx`, pas dans un fichier à lui. Le test
   * ci-dessus s'intitulait « les six panneaux » et n'en chargeait que cinq :
   * lui retirer `xl:relative` serait passé inaperçu. Contrôle post-release
   * des 0.48.x. Ici on vérifie le RENDU plutôt que le source — un panneau
   * qui a la classe mais ne s'affiche pas ne prouverait rien.
   */
  it('le canevas de contexte aussi, et c’est vérifié sur le rendu', async () => {
    reinitialiser();
    poserLargeurEcran(true);
    window.history.replaceState({}, '', '/?interface=conversation-canvas&scenario=meeting');
    render(<ConversationCanvasPrototype />);

    const panneau = await waitFor(() => {
      const noeud = document.querySelector(
        '[aria-labelledby="prototype-context-canvas-title"]',
      );
      expect(noeud).toBeTruthy();
      return noeud as HTMLElement;
    });

    expect(panneau.className).toContain('xl:relative');
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

describe('Revue Soso passe 5 - l’isolation d’un panneau ne déborde pas', () => {
  beforeEach(reinitialiser);

  it('P5-F1 : un panneau couvrant n’isole pas une modale ouverte par-dessus', async () => {
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

    // Une VRAIE modale s'ouvre par-dessus le panneau
    await act(async () => { runAction('shortcuts.open'); });
    const modale = await waitFor(() => {
      const n = document.querySelector('[role="dialog"][aria-modal="true"]');
      expect(n).toBeTruthy();
      return n as HTMLElement;
    });

    // ...puis la fenêtre passe sous le seuil : le panneau devient couvrant
    await act(async () => {
      coteACote = false;
      auditeurs.forEach((cb) => cb());
    });

    // Le panneau ne doit ni isoler la modale, ni lui voler le focus
    expect(modale.closest('[inert]')).toBeNull();
    expect(modale.getAttribute('aria-hidden')).not.toBe('true');
    expect(modale.contains(document.activeElement)).toBe(true);
  });

  it('P5-F2 : un focus sur le rail (non isolé) n’est pas transféré', async () => {
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

    // Le rail porte data-dialog-allow : il reste utilisable, donc le focus y reste
    const porteDuTiroir = screen.getByRole('button', { name: 'Plus d’outils' });
    porteDuTiroir.focus();

    await act(async () => {
      coteACote = false;
      auditeurs.forEach((cb) => cb());
    });

    expect(document.activeElement).toBe(porteDuTiroir);
  });
});

describe('Revue Soso passe 6 - l’isolation respecte l’ordre d’empilement', () => {
  it('P6-F1 : une modale isolante rend inerte la modale ouverte AVANT elle', async () => {
    const { useDialogFocusTrap } = await import('../../hooks/useDialogFocusTrap');
    const { useRef } = await import('react');

    function Dialogue({
      ouvert,
      testid,
      isole,
    }: {
      ouvert: boolean;
      testid: string;
      isole: boolean;
    }) {
      const ref = useRef<HTMLDivElement>(null);
      useDialogFocusTrap(ref, { active: ouvert, isolateBackground: isole });
      return ouvert ? (
        <div ref={ref} role="dialog" aria-modal="true" data-testid={testid}>
          <button type="button">{testid}</button>
        </div>
      ) : null;
    }

    function Page({ second }: { second: boolean }) {
      return (
        <div>
          {/* Ouverte en premier : elle est DESSOUS */}
          <Dialogue ouvert testid="raccourcis" isole={false} />
          {/* Ouverte ensuite : elle est DESSUS et isole le reste */}
          <Dialogue ouvert={second} testid="parametres" isole />
        </div>
      );
    }

    const { rerender } = render(<Page second={false} />);
    await waitFor(() => expect(screen.getByTestId('raccourcis')).toBeInTheDocument());

    rerender(<Page second />);
    await waitFor(() => expect(screen.getByTestId('parametres')).toBeInTheDocument());

    // La modale du DESSOUS doit être isolée par celle du dessus
    const dessous = screen.getByTestId('raccourcis');
    expect(dessous.closest('[inert]')).not.toBeNull();
    // ...et celle du dessus reste vivante
    expect(screen.getByTestId('parametres').closest('[inert]')).toBeNull();
  });
});

describe('Auto-contrôle - le z-order suit les règles du navigateur', () => {
  it('un z-index sur un élément non positionné n’a aucun effet', async () => {
    const { useDialogFocusTrap } = await import('../../hooks/useDialogFocusTrap');
    const { useRef } = await import('react');

    function Page() {
      const ref = useRef<HTMLDivElement>(null);
      useDialogFocusTrap(ref, { active: true, isolateBackground: true });
      return (
        <div>
          {/* z-index élevé MAIS position static : sans effet visuel, donc
              cette surface est bien derrière et doit être isolée. */}
          <div
            data-testid="faux-dessus"
            style={{ position: 'static', zIndex: 999 }}
          >
            <div role="dialog">Décor</div>
          </div>
          <div ref={ref} role="dialog" aria-modal="true" style={{ position: 'fixed', zIndex: 70 }}>
            <button type="button">Vraie modale</button>
          </div>
        </div>
      );
    }

    render(<Page />);
    await waitFor(() => {
      expect(screen.getByTestId('faux-dessus').closest('[inert]')).not.toBeNull();
    });
  });
});

/**
 * B-204 - le tiroir Conversations avait échappé aux deux gardes ci-dessus.
 *
 * Constat du 02/09/2026 (reproduction RP13c) : à 1280 px, où la propre règle
 * de l'application dit « côte à côte, ne pas recouvrir »
 * (`usePanneauCouvrant.ts` : SEUIL_COTE_A_COTE = 1280), ouvrir le tiroir
 * posait `inert` ET `aria-hidden="true"` sur `<main id="main-content">`, et le
 * tiroir se déclarait `role="dialog"` + `aria-modal="true"` - exactement ce
 * que le hotfix 0.48.1 avait proscrit.
 *
 * Cause de la NON-DÉTECTION : les deux gardes énumèrent des fichiers PAR NOM
 * (six `*Canvas.tsx` plus un cas spécial). `*Drawer.tsx` n'y figurait pas.
 * C'est le mode d'échec que `RolesDesPanneaux.test.ts` décrit lui-même pour le
 * canevas de contexte : « la liste ne pouvait pas le voir ». D'où la garde de
 * STRUCTURE qui suit, qui ne nomme personne.
 */
describe('B-204 - le tiroir Conversations est un panneau, pas une modale', () => {
  beforeEach(reinitialiser);

  async function ouvrirLeTiroir() {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('conversations.toggle'); });
    return waitFor(() => screen.getByTestId('prototype-conversation-drawer'));
  }

  it('grand écran : la colonne principale reste vivante', async () => {
    poserLargeurEcran(true);
    await ouvrirLeTiroir();

    const principale = document.getElementById('main-content');
    expect(principale, 'la colonne principale est introuvable').toBeTruthy();
    expect(principale!.hasAttribute('inert')).toBe(false);
    expect(principale!.getAttribute('aria-hidden')).not.toBe('true');
  });

  it('il ne se déclare jamais modal, à aucune largeur', async () => {
    poserLargeurEcran(false);
    const tiroir = await ouvrirLeTiroir();

    expect(tiroir.getAttribute('aria-modal')).not.toBe('true');
    expect(tiroir.getAttribute('role')).not.toBe('dialog');
  });

  it('petit écran : là, il isole bien la colonne qu’il recouvre', async () => {
    // Témoin : sans lui, retirer l'isolation partout passerait au vert.
    poserLargeurEcran(false);
    await ouvrirLeTiroir();

    const principale = document.getElementById('main-content');
    expect(principale!.hasAttribute('inert')).toBe(true);
  });

  it('il n’entre pas dans la pile des pièges clavier (S1-3)', async () => {
    const { trapStackTaille } = await import('../../hooks/useDialogFocusTrap');
    poserLargeurEcran(true);
    await ouvrirLeTiroir();

    expect(trapStackTaille()).toBe(0);
  });

  it('une modale ouverte PAR-DESSUS garde Échap (S1-3)', async () => {
    // Le piège du tiroir sortait de la pile des pièges : sa cascade Échap doit
    // donc passer ailleurs. Si elle se plaçait devant TOUT dans la cascade de
    // la coque, le tiroir volerait Échap aux Réglages ouverts au-dessus - le
    // défaut même que S1-3 décrit. Les Réglages piègent le focus mais ne
    // traitent pas Échap : c'est la cascade qui les ferme.
    poserLargeurEcran(true);
    await ouvrirLeTiroir();

    await act(async () => { usePanelStore.getState().openSettings(); });
    await waitFor(() => expect(usePanelStore.getState().showSettings).toBe(true));

    await act(async () => { fireEvent.keyDown(window, { key: 'Escape' }); });

    expect(usePanelStore.getState().showSettings).toBe(false);
    expect(screen.queryByTestId('prototype-conversation-drawer')).not.toBeNull();
  });

  it('Échap le ferme toujours, par le vrai chemin clavier de la coque', async () => {
    // Le piège de focus consommait Échap ; il ne le fait plus. C'est la pile
    // d'Échap de l'application qui porte la cascade, et la coque l'appelle en
    // premier. Mesuré sur une VRAIE frappe, dans la coque montée.
    poserLargeurEcran(true);
    await ouvrirLeTiroir();

    await act(async () => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });

    await waitFor(() =>
      expect(screen.queryByTestId('prototype-conversation-drawer')).toBeNull(),
    );
  });
});

/**
 * B-277 - isoler sans le dire : le tiroir posait `inert` sans monter le voile.
 *
 * Constat du 03/09/2026 (ronde de plateau B, 1279 px) : ouvrir le tiroir des
 * conversations passait `<main id="main-content">` à `inert` - le fond ne
 * répondait plus - alors qu'aucun voile ne le signalait. Le fond restait à
 * pleine luminosité : une application figée, pas une surface mise de côté.
 *
 * B-204 avait aligné le tiroir sur ses six frères pour la MOITIÉ isolation
 * (`usePanneauCouvrant`), mais la seconde moitié du contrat 0.48.1 - « si le
 * fond est isolé, il doit se VOIR » - passe par une liste de panneaux
 * ÉNUMÉRÉS PAR NOM dans la coque (`panneauLateralOuvert`), où le tiroir ne
 * figurait pas. Même mode d'échec que B-204, sur l'autre versant.
 *
 * L'invariant testé ici est donc le lien, pas l'un des deux bouts :
 * isolement et voile montent et tombent ENSEMBLE.
 */
describe('B-277 - le tiroir qui isole monte aussi le voile', () => {
  beforeEach(reinitialiser);

  async function ouvrirLeTiroir() {
    render(<ConversationCanvasPrototype />);
    await act(async () => { runAction('conversations.toggle'); });
    return waitFor(() => screen.getByTestId('prototype-conversation-drawer'));
  }

  it('1279 px : la colonne est isolée, donc le voile est monté', async () => {
    poserLargeurEcran(false);
    await ouvrirLeTiroir();

    const principale = document.getElementById('main-content');
    expect(principale, 'la colonne principale est introuvable').toBeTruthy();
    // Témoin : si le tiroir n'isolait plus rien, exiger un voile ne voudrait
    // rien dire. C'est bien un fond MORT qu'on demande de rendre visible.
    expect(principale!.hasAttribute('inert')).toBe(true);
    expect(
      screen.queryByTestId('panneau-voile'),
      'la colonne est inerte mais rien ne le montre : fond mort à pleine luminosité',
    ).not.toBeNull();
  });

  it('1280 px : ni isolement ni voile - le tiroir est côte à côte', async () => {
    poserLargeurEcran(true);
    await ouvrirLeTiroir();

    const principale = document.getElementById('main-content');
    expect(principale!.hasAttribute('inert')).toBe(false);
    expect(
      screen.queryByTestId('panneau-voile'),
      'un panneau côte à côte n’assombrit pas la conversation restée visible',
    ).toBeNull();
  });

  it('refermer le tiroir retire le voile avec l’isolement', async () => {
    poserLargeurEcran(false);
    await ouvrirLeTiroir();
    expect(screen.queryByTestId('panneau-voile')).not.toBeNull();

    await act(async () => { runAction('conversations.toggle'); });

    await waitFor(() =>
      expect(screen.queryByTestId('prototype-conversation-drawer')).toBeNull(),
    );
    expect(document.getElementById('main-content')!.hasAttribute('inert')).toBe(false);
    expect(screen.queryByTestId('panneau-voile')).toBeNull();
  });
});

/**
 * La garde qui ne nomme personne : un panneau latéral n'isole jamais sans condition.
 *
 * Les listes par NOM ont laissé passer le canevas de contexte (0.49) puis le
 * tiroir Conversations (B-204). On balaie donc TOUS les composants du dossier
 * `prototype/` : la géométrie de leur conteneur dit ce qu'ils sont. Une vraie
 * modale couvre l'écran entier (`inset-0` plus un voile) et peut isoler sans
 * condition ; un panneau latéral (`inset-y-0`, collé à un bord) ne le peut pas,
 * puisque la colonne qu'il laisse visible reste utilisable au-dessus du seuil.
 */
describe('Garde de structure : aucun panneau latéral n’isole sans condition', () => {
  it('balaie le dossier prototype/ sans citer un seul nom de fichier', async () => {
    const modules = import.meta.glob('./*.tsx', { query: '?raw', import: 'default', eager: true });

    const fautifs: string[] = [];
    for (const [chemin, source] of Object.entries(modules)) {
      if (chemin.includes('.test.')) continue;
      // Un composant à la fois : `isolateBackground: true` d'une modale ne
      // doit pas être imputé au panneau latéral rendu dans le même fichier.
      const composants = (source as string).split(/\n(?=(?:export )?function )/);
      for (const composant of composants) {
        if (!composant.includes('useDialogFocusTrap(')) continue;
        if (!composant.includes('isolateBackground: true')) continue;
        // `inset-y-0` sans `inset-0` : la signature d'un panneau de bord.
        if (!/className="[^"]*\binset-y-0\b/.test(composant)) continue;
        fautifs.push(`${chemin} : ${composant.split('\n')[0].trim()}`);
      }
    }

    expect(fautifs, 'panneau(x) latéral(aux) isolant la page sans condition de largeur').toEqual([]);
  });
});
