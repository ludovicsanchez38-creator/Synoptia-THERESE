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

function isolateOutsideDialog(dialog: HTMLElement): () => void {
  const isolated: HTMLElement[] = [];
  let branch: HTMLElement = dialog;
  let parent = branch.parentElement;

  while (parent && parent !== document.body) {
    for (const sibling of Array.from(parent.children)) {
      if (!(sibling instanceof HTMLElement) || sibling === branch) continue;
      if (sibling.matches('[data-dialog-backdrop], [data-dialog-allow]')) continue;
      isolateElement(sibling);
      isolated.push(sibling);
    }
    branch = parent;
    parent = parent.parentElement;
  }

  return () => isolated.reverse().forEach(restoreElement);
}

interface DialogFocusTrapOptions {
  /** Le piège n'est actif que si true (modale ouverte) */
  active: boolean;
  /** Appelé sur Escape ; omettre pour ne pas fermer à Escape */
  onEscape?: () => void;
  /** Isole le reste de l'application avec inert + aria-hidden. */
  isolateBackground?: boolean;
}

export function useDialogFocusTrap(
  ref: RefObject<HTMLElement | null>,
  { active, onEscape, isolateBackground = false }: DialogFocusTrapOptions
): void {
  // Lire onEscape via un ref : son identité ne doit pas réarmer le piège
  const onEscapeRef = useRef<(() => void) | undefined>(onEscape);
  onEscapeRef.current = onEscape;
  const hasEscape = Boolean(onEscape);

  useEffect(() => {
    if (!active) return;

    const dialog = ref.current;
    if (!dialog) return;

    const trapId = Symbol('dialog-trap');
    trapStack.push(trapId);
    const restoreIsolation = isolateBackground ? isolateOutsideDialog(dialog) : () => undefined;

    // Mémoriser l'élément déclencheur pour lui rendre le focus à la fermeture
    const previouslyFocused = document.activeElement as HTMLElement | null;

    // Focus initial : ne pas voler le focus s'il est déjà dans le dialogue
    // (ex : autoFocus posé par la modale sur un champ précis)
    if (!dialog.contains(document.activeElement)) {
      const preferred = dialog.querySelector<HTMLElement>('[data-dialog-autofocus]');
      const firstFocusable = dialog.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (preferred ?? firstFocusable ?? dialog).focus();
    }

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
      restoreIsolation();
      // WCAG : restaurer le focus à l'élément qui a ouvert la modale
      if (previouslyFocused && document.contains(previouslyFocused)) {
        previouslyFocused.focus();
      }
    };
    // hasEscape (booléen stable) plutôt que onEscape (identité instable) :
    // l'effet ne se réarme pas à chaque rendu du parent.
  }, [active, hasEscape, isolateBackground, ref]);
}
