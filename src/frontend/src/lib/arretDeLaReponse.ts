/**
 * Arrêt de la réponse en cours, joignable hors du composeur.
 *
 * B-1369 (persona Hugo, cycle 13) : le bandeau « Réponse en cours. Arrête la
 * réponse avant de changer de vue » s'affiche en bas à droite, par-dessus le
 * bouton « Arrêter la réponse » du composeur. Le composeur qui tient le flux
 * (son `AbortController` et l'annulation serveur) inscrit ici son arrêt, et le
 * bandeau le propose en bouton.
 */
let arret: (() => void) | null = null;

/** Inscrit l'arrêt du composeur monté ; renvoie la fonction qui le retire. */
export function inscrireArretDeLaReponse(fonction: () => void): () => void {
  arret = fonction;
  return () => {
    // Un composeur démonté après le montage d'un autre ne retire pas l'arrêt
    // du nouveau.
    if (arret === fonction) arret = null;
  };
}

/** Arrête la réponse en cours ; `false` si aucun composeur ne tient de flux. */
export function arreterLaReponse(): boolean {
  if (!arret) return false;
  arret();
  return true;
}

/** Le bouton « Arrêter la réponse » d'un bandeau, s'il peut agir. */
export function actionArreterLaReponse(): { label: string; onClick: () => void } | undefined {
  return arret ? { label: 'Arrêter la réponse', onClick: () => { arreterLaReponse(); } } : undefined;
}
