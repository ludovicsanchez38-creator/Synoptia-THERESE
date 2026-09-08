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

/**
 * B-637 (persona Nadia, c4) : la palette de la coque affiche plusieurs listes
 * à la suite (capacités, puis commandes de l'application). Chaque liste est
 * classée, mais la sélection initiale doit viser la meilleure correspondance
 * TOUTES listes confondues : « Conversations » désigne la commande du même
 * nom, pas la capacité dont la description contient le mot. Retourne l'index
 * plat (listes concaténées) ; 0 sans recherche ou sans correspondance. À rang
 * égal, la liste placée devant garde la main.
 */
export function indexDeLaMeilleureOption(
  groupes: readonly (readonly CommandeClassable[])[],
  recherche: string,
): number {
  const q = replierPourRecherche(recherche.trim());
  if (!q) return 0;
  let meilleur = { index: 0, rang: Number.POSITIVE_INFINITY };
  let decalage = 0;
  for (const groupe of groupes) {
    groupe.forEach((commande, i) => {
      const r = rang(commande, q);
      if (r >= 0 && r < meilleur.rang) meilleur = { index: decalage + i, rang: r };
    });
    decalage += groupe.length;
  }
  return meilleur.index;
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
