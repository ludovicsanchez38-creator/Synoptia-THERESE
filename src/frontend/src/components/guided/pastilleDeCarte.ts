/**
 * Les couleurs des pastilles des cartes d'action.
 *
 * 01/09/2026 : `ActionCard` construisait `var(--k1)` à `var(--k4)` et leurs
 * variantes de fond À L'EXÉCUTION. Ces jetons ont zéro définition dans
 * `globals.css`, dont le commentaire dit qu'ils vivent désormais sous
 * `--color-domaine-*`. Les pastilles n'avaient donc ni fond ni couleur.
 *
 * Un nom de variable assemblé à l'exécution est invisible à une recherche de
 * texte : c'est pour cela que l'audit graphique des 0.60 et 0.61 l'a manqué.
 * Les jetons sont donc écrits en toutes lettres ici, et un test les confronte
 * à la charte.
 */
export const JETONS_DE_PASTILLE = [
  '--color-domaine-agenda',
  '--color-domaine-taches',
  '--color-domaine-factures',
  '--color-domaine-prospects',
] as const;

export function jetonDePastille(index: number): { teinte: string; fond: string } {
  const base = JETONS_DE_PASTILLE[Math.abs(index) % JETONS_DE_PASTILLE.length];
  return { teinte: `var(${base})`, fond: `var(${base}-tint)` };
}
