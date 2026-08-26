/**
 * L'établi (B1, 0.48) — source unique des actions de l'accueil.
 *
 * CINQ actions, ids et destinations FIGÉS (les ids sont les scénarios
 * réels de la coque et des liens profonds ?scenario=). La palette ⌘K et
 * « Essayer un autre parcours » suivent cette liste ; les anciennes puces
 * priorités et mission vivent au tiroir (« Plus d'outils »).
 *
 * « Décider » a rejoint l'établi le 26/08/2026 : le Board est la capacité
 * la plus distinctive du produit et le seul geste de RECUL parmi quatre
 * verbes d'exécution ; au tiroir, personne ne le découvrait. Le principe
 * « un établi, un tiroir » borne l'accueil à peu d'actions, il ne fixe
 * pas leur nombre — mais l'établi n'est pas une étagère : toute action
 * ajoutée ici doit être un geste qu'on refait, pas une capacité de plus.
 */
import { Calendar, Gavel, Mail, Receipt, Users, type LucideIcon } from 'lucide-react';

export type IdEtabli = 'email' | 'memory' | 'meeting' | 'invoice' | 'board';

export interface ActionEtabli {
  id: IdEtabli;
  label: string;
}

export const ACTIONS_ETABLI: readonly ActionEtabli[] = [
  { id: 'email', label: 'Écrire' },
  { id: 'memory', label: 'Retrouver' },
  { id: 'meeting', label: 'Préparer' },
  { id: 'invoice', label: 'Facturer' },
  { id: 'board', label: 'Décider' },
];

/**
 * Une icône par action, table EXHAUSTIVE (`Record<IdEtabli, …>` : un id
 * sans icône ne compile pas). Elle remplace la cascade de ternaires de la
 * palette, dont la branche finale servait de fourre-tout — une action
 * ajoutée y héritait silencieusement de l'icône de la facture.
 */
export const ICONES_ETABLI: Record<IdEtabli, LucideIcon> = {
  email: Mail,
  memory: Users,
  meeting: Calendar,
  invoice: Receipt,
  board: Gavel,
};

/** Le placeholder INACTIF partagé des deux composeurs (chat + coque). */
export const PLACEHOLDER_COMPOSEUR = 'Demande à Thérèse d’organiser, créer ou agir…';
