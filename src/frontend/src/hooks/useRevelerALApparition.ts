/**
 * Un message ou une confirmation qui apparaît au bas d'un contenu défilant
 * reste souvent hors de la zone visible : le geste paraît sans effet (B-1030,
 * B-1032). À son apparition, l'élément est amené dans la vue ; une
 * confirmation qui remplace le bouton cliqué reçoit aussi le focus, sinon il
 * tombe sur la page (B-1030, B-1034).
 *
 * `cle` : toute valeur vraie affiche l'élément ; une nouvelle valeur (un autre
 * message d'erreur) le révèle de nouveau.
 */
import { useEffect, useRef } from 'react';

type Focus = false | 'element' | 'premier-bouton';

export function useRevelerALApparition<T extends HTMLElement = HTMLDivElement>(
  cle: unknown,
  focus: Focus = false,
) {
  const ref = useRef<T>(null);
  useEffect(() => {
    if (!cle) return;
    const element = ref.current;
    if (!element) return;
    // Absent de certains moteurs de test : l'appel reste facultatif.
    element.scrollIntoView?.({ block: 'nearest' });
    if (focus === 'premier-bouton') {
      element.querySelector<HTMLElement>('button:not([disabled])')?.focus();
    } else if (focus === 'element') {
      element.focus();
    }
  }, [cle, focus]);
  return ref;
}
