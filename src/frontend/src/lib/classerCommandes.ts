/**
 * Classement des commandes de la palette (B-613, persona Karim) : une
 * correspondance sur le NOM passe avant une correspondance sur un mot-clé, qui
 * passe avant une correspondance sur la description. Taper « Conversations »
 * ouvrait « Tâches », dont la description contenait le mot.
 */
import { replierPourRecherche } from './replierPourRecherche';

export interface CommandeClassable {
  name: string;
  description?: string;
  keywords?: string[];
}


function rang(commande: CommandeClassable, q: string): number {
  const nom = replierPourRecherche(commande.name);
  if (nom === q) return 0;
  if (nom.startsWith(q)) return 1;
  if (nom.includes(q)) return 2;
  if ((commande.keywords ?? []).some((k) => replierPourRecherche(k).includes(q))) return 3;
  if (replierPourRecherche(commande.description ?? '').includes(q)) return 4;
  return -1;
}

export function classerCommandes<T extends CommandeClassable>(commandes: readonly T[], recherche: string): T[] {
  const q = replierPourRecherche(recherche.trim());
  if (!q) return [...commandes];
  return commandes
    .map((c, i) => ({ c, i, r: rang(c, q) }))
    .filter((x) => x.r >= 0)
    .sort((a, b) => a.r - b.r || a.i - b.i)
    .map((x) => x.c);
}
