/**
 * Hotfix 0.48.1 - un panneau latéral n'est modal que s'il couvre l'écran.
 *
 * Les panneaux de la coque (contexte de scénario, outils, vues embarquées)
 * sont côte à côte au-delà du seuil `xl` de Tailwind, et RECOUVRENT la zone
 * principale en dessous. L'isolation du fond et le piégeage du clavier ne
 * valent que dans le second cas : sinon ils tuent la colonne principale, que
 * l'utilisateur voit pourtant à côté (bug signalé le 25/08).
 *
 * Revue Soso (S1-1) : « couvrant » n'est PAS « modal ». Le rail et l'en-tête
 * restent volontairement actifs (navigation permanente, `data-dialog-allow`) ;
 * un panneau ne peut donc jamais porter `aria-modal` sans mentir. Il isole la
 * zone qu'il recouvre, rien de plus.
 */
import { useEffect, useState } from 'react';

/** Seuil `xl` de Tailwind - celui qu'utilisent déjà les classes des panneaux. */
export const SEUIL_COTE_A_COTE = 1280;

const REQUETE = `(min-width: ${SEUIL_COTE_A_COTE}px)`;

function estCoteACote(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia(REQUETE).matches;
}

/** true quand le panneau RECOUVRE la zone principale (sous le seuil xl). */
export function usePanneauCouvrant(): boolean {
  const [couvrant, setCouvrant] = useState(() => !estCoteACote());

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia(REQUETE);
    const surChangement = () => setCouvrant(!mq.matches);
    surChangement();
    // Safari < 14 n'a que addListener ; le mock de tests expose les deux.
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', surChangement);
      return () => mq.removeEventListener('change', surChangement);
    }
    mq.addListener?.(surChangement);
    return () => mq.removeListener?.(surChangement);
  }, []);

  return couvrant;
}
