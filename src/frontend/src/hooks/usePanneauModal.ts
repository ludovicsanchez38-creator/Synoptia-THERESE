/**
 * Hotfix 0.48.1 - un panneau latéral n'est modal que s'il couvre l'écran.
 *
 * Les panneaux de la coque (contexte de scénario, outils, vues embarquées)
 * sont côte à côte au-delà du seuil `xl` de Tailwind, et plein écran en
 * dessous. Le comportement modal (isolation du fond, piégeage du clavier)
 * ne vaut que dans le second cas : sinon il tue la colonne principale, que
 * l'utilisateur voit pourtant à côté (bug signalé le 25/08).
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

/** true quand le panneau couvre l'écran : il doit alors se comporter en modale. */
export function usePanneauModal(): boolean {
  const [modal, setModal] = useState(() => !estCoteACote());

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia(REQUETE);
    const surChangement = () => setModal(!mq.matches);
    surChangement();
    // Safari < 14 n'a que addListener ; le mock de tests expose les deux.
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', surChangement);
      return () => mq.removeEventListener('change', surChangement);
    }
    mq.addListener?.(surChangement);
    return () => mq.removeListener?.(surChangement);
  }, []);

  return modal;
}
