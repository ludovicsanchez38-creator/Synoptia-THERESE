/**
 * Slug d'une commande utilisateur (B-595) : les lettres accentuées sont
 * ramenées à leur base (« Résumé » -> « resume »), et un nom qui ne laisse
 * aucun caractère utilisable devient « commande » plutôt qu'une chaîne vide.
 */
export function slugDeCommande(nom: string): string {
  const base = nom
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return base || 'commande';
}
