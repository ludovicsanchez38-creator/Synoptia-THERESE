/**
 * B-278 - la palette de commandes n'est plus un cul-de-sac pour le focus.
 *
 * Mesuré en ronde de plateau A3 : ⌘K depuis un bouton du rail puis Échap
 * laissait `document.activeElement` sur BODY, et toute surface ouverte DEPUIS
 * la palette perdait elle aussi le retour du focus, alors que la même surface
 * ouverte directement depuis le rail le rendait bien.
 *
 * La palette appelle pourtant `useDialogFocusTrap` depuis longtemps. La cause
 * n'est pas l'absence du piège mais l'attribut `autoFocus` de son champ de
 * recherche : React le pose pendant la phase de commit, donc AVANT les effets
 * passifs du hook. Quand l'effet 1 s'exécute, le focus est déjà DANS le
 * dialogue, sa garde `if (!dialog.contains(document.activeElement))`
 * (useDialogFocusTrap.ts) saute, et le déclencheur n'est jamais mémorisé.
 * `data-dialog-autofocus` désigne déjà ce même champ au hook : la destination
 * du focus initial ne change pas, seule la capture du déclencheur revient.
 *
 * Contrat, identique à B-251 (ExternalActionConfirmation) et B-262 (CRM) :
 * une surface modale rend le focus à ce qui l'a ouverte.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

/** Même dérivation que `useKeyboardShortcuts` : ⌘ sur Mac, Ctrl ailleurs. */
const MODIFICATEUR = navigator.platform.toUpperCase().includes('MAC')
  ? { metaKey: true }
  : { ctrlKey: true };

/** Décrit l'élément actif d'une façon lisible dans un message d'échec. */
function actif(): string {
  const noeud = document.activeElement as HTMLElement | null;
  if (!noeud) return 'aucun';
  const nom = noeud.getAttribute('aria-label') ?? noeud.textContent?.trim() ?? '';
  return `${noeud.tagName}${nom ? ` « ${nom.slice(0, 40)} »` : ''}`;
}

/**
 * Le rail est le déclencheur décrit par la fiche.
 *
 * Le `<nav>` porte bien `data-dialog-allow`, mais cela ne l'épargne PAS ici :
 * `isolateOutsideDialog` ne lit cet attribut que sur les frères DIRECTS de la
 * branche du dialogue, et la palette est montée à la racine - c'est l'ancêtre
 * `div.flex.h-full.flex-col` qui est isolé, rail compris. Mesuré au navigateur
 * (`bouton.closest('[inert]')` vaut le conteneur pendant que la palette est
 * ouverte, et null après Échap). Ce test-ci ne peut pas le voir : jsdom
 * n'implémente pas `inert`. C'est donc la mesure Playwright, et elle seule, qui
 * prouve que l'isolation tombe AVANT la restauration du focus (l'ordre des
 * quatre effets de useDialogFocusTrap) ; ici on ne mesure que la capture du
 * déclencheur.
 */
function railProjets(): HTMLElement {
  return screen.getByRole('button', { name: 'Projets' });
}

describe('B-278 - la palette rend le focus à son déclencheur', () => {
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

  it('Échap depuis la palette ouverte au clavier rend le focus au bouton du rail', () => {
    render(<ConversationCanvasPrototype />);
    const declencheur = railProjets();
    declencheur.focus();
    expect(document.activeElement, 'le déclencheur doit tenir le focus AVANT ⌘K').toBe(declencheur);

    fireEvent.keyDown(window, { key: 'k', ...MODIFICATEUR });
    const palette = screen.getByRole('dialog', { name: 'Rechercher dans Thérèse' });
    expect(palette.contains(document.activeElement), 'la palette doit prendre le focus').toBe(true);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(document.activeElement, `focus laissé sur ${actif()}`).toBe(declencheur);
  });

  it('le tiroir ouvert DEPUIS la palette rend le focus comme ouvert directement', () => {
    render(<ConversationCanvasPrototype />);
    const declencheur = railProjets();
    declencheur.focus();
    fireEvent.keyDown(window, { key: 'k', ...MODIFICATEUR });

    const champ = screen.getByRole('combobox', {
      name: 'Rechercher une commande, un parcours ou une capacité',
    });
    fireEvent.change(champ, { target: { value: 'liste des conversations' } });
    const option = screen.getByRole('option', { name: /Ouvrir la liste des conversations/ });
    fireEvent.click(option);

    expect(screen.getByTestId('prototype-conversation-drawer')).toBeTruthy();

    // Le tiroir n'a pas de piège clavier : c'est la cascade de la coque, sur
    // `window`, qui le ferme.
    fireEvent.keyDown(window, { key: 'Escape' });

    expect(document.activeElement, `focus laissé sur ${actif()}`).toBe(declencheur);
  });

  it('témoin : le tiroir ouvert DIRECTEMENT depuis le rail rendait déjà le focus', () => {
    // Contre-épreuve de l'instrument : ce chemin-là fonctionnait avant le
    // correctif. S'il rougissait, la mesure porterait sur le tiroir et non sur
    // la palette.
    render(<ConversationCanvasPrototype />);
    const declencheur = screen.getByRole('button', { name: 'Conversations' });
    declencheur.focus();
    fireEvent.click(declencheur);

    expect(screen.getByTestId('prototype-conversation-drawer')).toBeTruthy();
    fireEvent.keyDown(window, { key: 'Escape' });

    expect(document.activeElement, `focus laissé sur ${actif()}`).toBe(declencheur);
  });
});
