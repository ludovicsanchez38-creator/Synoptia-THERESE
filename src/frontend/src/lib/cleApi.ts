/**
 * Saisie d'une clé d'API (audit bêta du 27/10/2026, A2-22).
 *
 * Une copie emporte souvent une espace ou un retour à la ligne : on contrôle
 * et on envoie ce que l'utilisateur lit, comme le moteur (B-510). Une seule
 * règle pour l'accueil et les Paramètres.
 */
export function nettoyerCle(saisie: string): string {
  return saisie.trim();
}
