/**
 * US-013 : piégeage du focus pour les dialogues modaux (WCAG 2.4.3 / ARIA APG).
 *
 * Source unique de vérité du comportement modal clavier :
 * - focus initial sur le premier élément focusable à l'ouverture
 * - Tab/Shift+Tab bouclent à l'intérieur du dialogue
 * - Escape ferme (optionnel - les wizards multi-étapes peuvent s'en passer)
 * - le focus REVIENT à l'élément déclencheur à la fermeture
 *
 * Durci après revue adversariale :
 * - PILE PARTAGÉE : quand deux modales DOM-disjointes sont ouvertes en même
 *   temps (ex. Settings + raccourcis Cmd+/), seul le piège du DESSUS traite
 *   Tab/recapture/Escape - sinon les deux se volaient le focus à chaque Tab.
 * - onEscape lu via un ref : une closure recréée à chaque rendu du parent ne
 *   réarme plus l'effet (le focus ne saute plus pendant la saisie), et la
 *   restauration du focus n'a lieu qu'à la fermeture réelle.
 *
 * Utilisé par DialogShell et appliqué aux modales artisanales.
 */
import { useEffect, useRef, type RefObject } from 'react';

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])';

// Pile des pièges actifs (même principe que escapeStack) : le dernier
// enregistré est la modale du dessus, seule autorisée à piloter le clavier.
const trapStack: symbol[] = [];

interface IsolatedElementState {
  count: number;
  inert: boolean;
  inertAttribute: string | null;
  ariaHidden: string | null;
}

const isolatedElements = new WeakMap<HTMLElement, IsolatedElementState>();

function isolateElement(element: HTMLElement): void {
  const existing = isolatedElements.get(element);
  if (existing) {
    existing.count += 1;
    return;
  }

  isolatedElements.set(element, {
    count: 1,
    inert: element.inert,
    inertAttribute: element.getAttribute('inert'),
    ariaHidden: element.getAttribute('aria-hidden'),
  });
  element.inert = true;
  element.setAttribute('inert', '');
  element.setAttribute('aria-hidden', 'true');
}

function restoreElement(element: HTMLElement): void {
  const state = isolatedElements.get(element);
  if (!state) return;
  state.count -= 1;
  if (state.count > 0) return;

  element.inert = state.inert;
  if (state.inertAttribute === null) element.removeAttribute('inert');
  else element.setAttribute('inert', state.inertAttribute);
  if (state.ariaHidden === null) element.removeAttribute('aria-hidden');
  else element.setAttribute('aria-hidden', state.ariaHidden);
  isolatedElements.delete(element);
}

/**
 * Un élément est-il visuellement AU-DESSUS d'un autre ?
 *
 * Revue passe 7 (F1) : l'ordre d'OUVERTURE ne dit rien de l'ordre VISUEL -
 * une modale ouverte en second peut être rendue derrière. Ce qui fait foi,
 * c'est le z-index effectif, puis l'ordre du DOM à z-index égal (règle de
 * peinture du navigateur).
 */
function estAuDessus(candidat: HTMLElement, reference: HTMLElement): boolean {
  const z = (element: HTMLElement): number => {
    for (let noeud: HTMLElement | null = element; noeud; noeud = noeud.parentElement) {
      const brut = window.getComputedStyle(noeud).zIndex;
      const valeur = Number.parseInt(brut, 10);
      if (!Number.isNaN(valeur)) return valeur;
    }
    return 0;
  };

  const zCandidat = z(candidat);
  const zReference = z(reference);
  if (zCandidat !== zReference) return zCandidat > zReference;
  // z-index égal (ou indisponible) : le dernier peint gagne, donc l'ordre DOM.
  return Boolean(
    reference.compareDocumentPosition(candidat) & Node.DOCUMENT_POSITION_FOLLOWING,
  );
}

/**
 * Isole tout ce qui entoure le dialogue, et rend la liste RÉELLEMENT isolée.
 *
 * Revue passe 5 (F1) : une vraie modale ouverte PAR-DESSUS est rendue à côté
 * de la coque ; un panneau qui devient couvrant l'isolait donc elle aussi -
 * elle se retrouvait inerte et sans focus possible. Ce qui porte `aria-modal`
 * est au-dessus par définition : on ne l'isole jamais.
 */
function isolateOutsideDialog(dialog: HTMLElement): {
  isoles: HTMLElement[];
  restaurer: () => void;
} {
  const isolated: HTMLElement[] = [];
  let branch: HTMLElement = dialog;
  let parent = branch.parentElement;

  while (parent && parent !== document.body) {
    for (const sibling of Array.from(parent.children)) {
      if (!(sibling instanceof HTMLElement) || sibling === branch) continue;
      if (sibling.matches('[data-dialog-backdrop], [data-dialog-allow]')) continue;
      // Épargner uniquement ce qui est VISUELLEMENT au-dessus (passe 7, F1) :
      // une surface rendue derrière doit être isolée comme le reste du fond.
      const dialoguesDuFrere: HTMLElement[] = [
        ...(sibling.matches('[role="dialog"]') ? [sibling] : []),
        ...Array.from(sibling.querySelectorAll<HTMLElement>('[role="dialog"]')),
      ];
      if (dialoguesDuFrere.some((autre) => estAuDessus(autre, dialog))) {
        continue;
      }
      isolateElement(sibling);
      isolated.push(sibling);
    }
    branch = parent;
    parent = parent.parentElement;
  }

  return {
    isoles: isolated,
    restaurer: () => isolated.reverse().forEach(restoreElement),
  };
}

interface DialogFocusTrapOptions {
  /** Le piège n'est actif que si true (modale ouverte) */
  active: boolean;
  /** Appelé sur Escape ; omettre pour ne pas fermer à Escape */
  onEscape?: () => void;
  /** Isole le reste de l'application avec inert + aria-hidden. */
  isolateBackground?: boolean;
  /**
   * Hotfix 0.48.1 : false pour un panneau CÔTE À CÔTE - focus initial et
   * restauration conservés, mais ni piégeage de Tab (l'utilisateur doit
   * pouvoir tabuler vers la colonne principale) ni capture d'Escape (la
   * cascade de la coque s'en charge). Défaut true = comportement modal.
   */
  piegeClavier?: boolean;
}

/** Sonde de test : combien de pièges clavier sont actifs (revue Soso S1-3). */
export function trapStackTaille(): number {
  return trapStack.length;
}

export function useDialogFocusTrap(
  ref: RefObject<HTMLElement | null>,
  { active, onEscape, isolateBackground = false, piegeClavier = true }: DialogFocusTrapOptions
): void {
  // Lire onEscape via un ref : son identité ne doit pas réarmer le piège
  const onEscapeRef = useRef<(() => void) | undefined>(onEscape);
  onEscapeRef.current = onEscape;
  const hasEscape = Boolean(onEscape);

  // Revue Soso passe 3 (finding 1) : TROIS responsabilités, TROIS effets aux
  // dépendances propres. Réunies dans un seul effet, un simple changement de
  // largeur (isolateBackground) réarmait aussi le cycle focus initial +
  // restauration : la saisie en cours perdait le focus au profit du titre.

  // L'ordre de DÉCLARATION compte : React nettoie les effets dans cet ordre.
  // Il faut donc que l'isolation soit retirée AVANT que le focus revienne au
  // déclencheur (passe 4, F2 : un focus() sur un élément encore `inert` est
  // ignoré par le navigateur et le focus finit sur BODY).
  const declencheurRef = useRef<HTMLElement | null>(null);

  // 1. Mémoriser le déclencheur, puis poser le focus initial dans le dialogue.
  //    La capture doit précéder tout déplacement de focus.
  useEffect(() => {
    if (!active) return;
    const dialog = ref.current;
    if (!dialog) return;

    if (!dialog.contains(document.activeElement)) {
      declencheurRef.current = document.activeElement as HTMLElement | null;
      const prefere = dialog.querySelector<HTMLElement>('[data-dialog-autofocus]');
      const premier = dialog.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (prefere ?? premier ?? dialog).focus();
    }
  }, [active, ref]);

  // 2. Isolation du fond - se réarme librement au changement de largeur.
  useEffect(() => {
    if (!active || !isolateBackground) return;
    const dialog = ref.current;
    if (!dialog) return;

    const { isoles, restaurer } = isolateOutsideDialog(dialog);
    // Passe 4 (F1) : si le focus se trouvait dans la zone qu'on vient d'isoler
    // (l'utilisateur écrivait quand la fenêtre est passée sous le seuil), il
    // DOIT suivre - sinon le champ paraît actif mais la frappe se perd.
    // Passe 5 (F2) : SEULEMENT dans ce cas - le rail et l'en-tête restent
    // utilisables (data-dialog-allow), une modale au-dessus garde son focus.
    const focusDansUneZoneIsolee = isoles.some((element) =>
      element.contains(document.activeElement),
    );
    if (focusDansUneZoneIsolee) {
      const prefere = dialog.querySelector<HTMLElement>('[data-dialog-autofocus]');
      const premier = dialog.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (prefere ?? premier ?? dialog).focus();
    }
    return restaurer;
  }, [active, isolateBackground, ref]);

  // 3. Restauration du focus - DÉCLARÉE APRÈS l'isolation, donc nettoyée
  //    après elle : le déclencheur n'est plus `inert` quand on le refocalise.
  useEffect(() => {
    if (!active) return;
    return () => {
      const declencheur = declencheurRef.current;
      declencheurRef.current = null;
      // WCAG : rendre le focus à l'élément qui a ouvert la modale
      if (declencheur && document.contains(declencheur)) {
        declencheur.focus();
      }
    };
  }, [active]);

  // 4. Pilotage du clavier (Tab bouclé, Escape) - modales seulement.
  useEffect(() => {
    if (!active || !piegeClavier) return;
    const dialog = ref.current;
    if (!dialog) return;

    const trapId = Symbol('dialog-trap');
    // Revue Soso S1-3 : un panneau côte à côte ne pilote pas le clavier - il
    // n'entre donc pas dans la pile. Sinon un réarmement le place au-dessus
    // d'une modale ouverte entre-temps et lui vole Escape.
    trapStack.push(trapId);

    function isTopmost(): boolean {
      return trapStack[trapStack.length - 1] === trapId;
    }

    function handleKeyDown(e: KeyboardEvent) {
      // Seule la modale du dessus pilote le clavier
      if (!isTopmost()) return;

      if (e.key === 'Escape' && onEscapeRef.current) {
        e.preventDefault();
        e.stopPropagation();
        onEscapeRef.current();
        return;
      }
      if (e.key !== 'Tab') return;

      const focusables = dialog!.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      // Focus sorti du dialogue (clic ailleurs) : Tab le ramène dedans
      if (!dialog!.contains(document.activeElement)) {
        e.preventDefault();
        first.focus();
        return;
      }

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      const idx = trapStack.indexOf(trapId);
      if (idx !== -1) trapStack.splice(idx, 1);
    };
    // hasEscape (booléen stable) plutôt que onEscape (identité instable) :
    // l'effet ne se réarme pas à chaque rendu du parent.
  }, [active, hasEscape, piegeClavier, ref]);
}
