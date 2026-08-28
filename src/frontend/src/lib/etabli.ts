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
 * Le TITRE de la surface qu'ouvre chaque verbe.
 *
 * Exporté ici, à côté des verbes eux-mêmes, pour qu'un test puisse APPARIER
 * les deux. La dérive de la v0.53.0 vient de leur éloignement : l'entrée 10 a
 * changé ce que « Écrire » fait, la table des titres est restée dans la coque,
 * et le canevas a continué de s'annoncer « Consulter mes emails » aux lecteurs
 * d'écran.
 *
 * `Record<IdEtabli, string>` : un verbe sans titre ne compile pas.
 */
export const TITRES_ETABLI: Record<IdEtabli, string> = {
  email: 'Écrire un message',
  memory: 'Retrouver un contact',
  meeting: 'Préparer un rendez-vous',
  invoice: 'Facturer un client',
  board: 'Éclairer une décision',
};

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
