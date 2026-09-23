/**
 * Saisies en cours qui retiennent une sortie de vue (B-978, cycle 11, 23/09/2026).
 *
 * Avec un formulaire Tâche ou Rendez-vous modifié, le « Retour » d'en-tête de
 * la vue et le rail refermaient la vue et jetaient la saisie sans question :
 * seuls Échap et le « Retour » du formulaire passaient par elle. Un
 * formulaire modifié s'inscrit ici ; la coque consulte le registre avant de
 * quitter une vue. Le formulaire le plus récent décide : s'il est modifié, il
 * pose sa question et la sortie est retenue.
 */

type Garde = () => boolean;

const gardes: Garde[] = [];

/** Inscrit un formulaire ; la garde rend vrai si elle retient la sortie. */
export function inscrireSaisieEnCours(garde: Garde): () => void {
  gardes.push(garde);
  return () => {
    const i = gardes.lastIndexOf(garde);
    if (i !== -1) gardes.splice(i, 1);
  };
}

/** Vrai si un formulaire modifié retient la sortie (il a alors posé sa question). */
export function sortieRetenueParUneSaisie(): boolean {
  for (let i = gardes.length - 1; i >= 0; i -= 1) {
    if (gardes[i]()) return true;
  }
  return false;
}

/** Réinitialise le registre (tests uniquement). */
export function _viderSaisiesEnCours(): void {
  gardes.length = 0;
}
