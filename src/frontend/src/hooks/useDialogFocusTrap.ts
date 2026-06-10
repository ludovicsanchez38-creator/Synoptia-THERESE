/**
 * US-013 : piégeage du focus pour les dialogues modaux (WCAG 2.4.3 / ARIA APG).
 *
 * Source unique de vérité du comportement modal clavier :
 * - focus initial sur le premier élément focusable à l'ouverture
 * - Tab/Shift+Tab bouclent à l'intérieur du dialogue
 * - Escape ferme (optionnel - les wizards multi-étapes peuvent s'en passer)
 * - le focus REVIENT à l'élément déclencheur à la fermeture
 *
 * Utilisé par DialogShell et appliqué aux modales artisanales
 * (SettingsModal, ContactModal, ProjectModal, etc.).
 */
import { useEffect, type RefObject } from 'react';

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])';

interface DialogFocusTrapOptions {
  /** Le piège n'est actif que si true (modale ouverte) */
  active: boolean;
  /** Appelé sur Escape ; omettre pour ne pas fermer à Escape */
  onEscape?: () => void;
}

export function useDialogFocusTrap(
  ref: RefObject<HTMLElement | null>,
  { active, onEscape }: DialogFocusTrapOptions
): void {
  useEffect(() => {
    if (!active) return;

    const dialog = ref.current;
    if (!dialog) return;

    // Mémoriser l'élément déclencheur pour lui rendre le focus à la fermeture
    const previouslyFocused = document.activeElement as HTMLElement | null;

    // Focus initial : ne pas voler le focus s'il est déjà dans le dialogue
    // (ex : autoFocus posé par la modale sur un champ précis)
    if (!dialog.contains(document.activeElement)) {
      const firstFocusable = dialog.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      firstFocusable?.focus();
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && onEscape) {
        e.stopPropagation();
        onEscape();
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
      // WCAG : restaurer le focus à l'élément qui a ouvert la modale
      if (previouslyFocused && document.contains(previouslyFocused)) {
        previouslyFocused.focus();
      }
    };
  }, [active, onEscape, ref]);
}
