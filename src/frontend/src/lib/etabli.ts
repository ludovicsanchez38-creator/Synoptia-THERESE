/**
 * L'établi (B1, 0.48) — source unique des actions de l'accueil.
 *
 * QUATRE actions, ids et destinations FIGÉS (les ids sont les scénarios
 * réels de la coque et des liens profonds ?scenario=). La palette ⌘K et
 * « Essayer un autre parcours » suivent cette liste ; les anciennes puces
 * priorités/décision/mission vivent au tiroir (« Plus d'outils »).
 */

export interface ActionEtabli {
  id: 'email' | 'memory' | 'meeting' | 'invoice';
  label: string;
}

export const ACTIONS_ETABLI: readonly ActionEtabli[] = [
  { id: 'email', label: 'Écrire' },
  { id: 'memory', label: 'Retrouver' },
  { id: 'meeting', label: 'Préparer' },
  { id: 'invoice', label: 'Facturer' },
];

/** Le placeholder INACTIF partagé des deux composeurs (chat + coque). */
export const PLACEHOLDER_COMPOSEUR = 'Demande à Thérèse d’organiser, créer ou agir…';
