/**
 * DA « Application affinée », lot 6 : la barre de priorité d'une tâche.
 *
 * La maquette remplace le mot (« Urgent », « Haute »…) par un trait vertical
 * coloré, le même en colonnes et en liste (`projets.html:22` et `:82`). Un
 * `div` sans rôle n'entre pas dans le calcul de nom accessible : la barre est
 * donc un `role="img"` nommé, sinon la priorité disparaîtrait pour qui
 * n'a pas l'écran.
 *
 * Les teintes sont les REMPLISSAGES de la maquette (`--color-error-fill`…),
 * pas les jetons d'encre : ce sont des aplats, pas du texte.
 *
 * Module sans composant : les deux vues le partagent, et un `.ts` garde
 * `react-refresh/only-export-components` silencieux.
 */

export interface BarrePriorite {
  classe: string;
  nom: string;
}

const BARRES: Record<string, BarrePriorite> = {
  urgent: { classe: 'bg-error-fill', nom: 'Priorité urgente' },
  high: { classe: 'bg-warning-fill', nom: 'Priorité haute' },
  medium: { classe: 'bg-info-fill', nom: 'Priorité moyenne' },
  low: { classe: 'bg-border', nom: 'Priorité basse' },
};

/** Forme commune aux deux vues : 4 px de large, la hauteur d'une ligne. */
export const CLASSE_BARRE_PRIORITE = 'w-1 h-[1.1rem] rounded-sm shrink-0';

/**
 * `null` pour une priorité inconnue : on n'invente pas de nom. Avant, le
 * kanban affichait dans ce cas une pastille bordée VIDE (`px-2 py-0.5 text-xs
 * rounded-sm border` sans classe de couleur ni texte) et la liste ne montrait
 * rien. Ne rien afficher vaut mieux qu'une pastille vide, et c'est désormais
 * le même silence dans les deux vues.
 */
export function barrePriorite(priorite: string | null | undefined): BarrePriorite | null {
  if (!priorite) return null;
  return BARRES[priorite] ?? null;
}
