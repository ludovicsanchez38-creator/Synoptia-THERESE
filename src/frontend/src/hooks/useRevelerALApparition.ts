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
import { useEffect, useRef, type RefObject } from 'react';

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

/**
 * B-1061 : une confirmation en ligne remplace souvent le bouton qui l'ouvre.
 * « Annuler » la démonte, alors qu'elle avait le focus : il tombait sur la
 * page. À la fermeture, le focus revient au déclencheur (remonté entre-temps),
 * sauf s'il est déjà parti ailleurs.
 */
export function useRendreLeFocusALaFermeture(
  ouvert: boolean,
  declencheurRef: RefObject<HTMLElement | null>,
) {
  const etaitOuvert = useRef(ouvert);
  useEffect(() => {
    const vientDeFermer = etaitOuvert.current && !ouvert;
    etaitOuvert.current = ouvert;
    if (!vientDeFermer) return;
    const actif = document.activeElement;
    if (!actif || actif === document.body || !actif.isConnected) declencheurRef.current?.focus();
  }, [ouvert, declencheurRef]);
}
