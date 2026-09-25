/**
 * Entrée dans un champ texte valide le formulaire (B-1365).
 *
 * Hugo et Zoé (cycle 13) : Entrée ne faisait rien dans six formulaires, seul
 * le devis réagissait. Pas de `<form>` : `Button` n'a pas de type par défaut,
 * et envelopper les champs aurait changé en boutons d'envoi ceux d'une
 * confirmation de suppression voisine. Le gestionnaire se pose sur le
 * conteneur des champs.
 *
 * Une zone de texte garde son retour à la ligne ; une case, un bouton ou un
 * sélecteur gardent leur comportement ; Maj, Ctrl, Alt, Cmd et la composition
 * de caractères (accents, IME) n'envoient rien.
 */
import type { KeyboardEvent } from 'react';

const TYPES_SANS_VALIDATION = new Set(['checkbox', 'radio', 'button', 'submit', 'reset', 'file', 'color', 'range']);

export function entreeValide(action: () => void, desactive = false) {
  return (e: KeyboardEvent<HTMLElement>) => {
    if (desactive || e.key !== 'Enter') return;
    if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey || e.nativeEvent.isComposing) return;
    const cible = e.target;
    if (!(cible instanceof HTMLInputElement) || TYPES_SANS_VALIDATION.has(cible.type)) return;
    e.preventDefault();
    action();
  };
}
