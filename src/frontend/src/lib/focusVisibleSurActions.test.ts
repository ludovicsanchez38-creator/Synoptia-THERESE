/**
 * E1 — un contrôle atteignable au clavier doit être visible quand il a le focus.
 *
 * Passe navigateur de la campagne, constat U1. Mesuré sur l'écran
 * *Devis et factures* :
 *
 *   { focusEstSurLeBouton: true, labelFocalise: "Supprimer",
 *     focusVisible: true, opaciteDuConteneur: "0" }
 *
 * Le navigateur veut afficher l'anneau de focus ; le conteneur est à
 * `opacity: 0`. L'utilisateur au clavier a donc le focus sur un bouton
 * **Supprimer** qu'il ne voit pas.
 *
 * En cherchant, le motif s'est révélé SYSTÉMIQUE : onze occurrences de
 * `opacity-0 group-hover:opacity-100` autour de boutons, dans neuf fichiers,
 * et pas une seule `group-focus-within`. Ce n'était pas un défaut de la liste
 * des factures : c'est une habitude de code.
 *
 * Ce test est un garde-fou de motif : il échoue dès qu'une nouvelle grappe
 * d'actions n'apparaît qu'au survol.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..');

function fichiersTsx(dossier: string): string[] {
  const trouves: string[] = [];
  for (const entree of readdirSync(dossier)) {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      trouves.push(...fichiersTsx(chemin));
    } else if (entree.endsWith('.tsx') && !entree.includes('.test.')) {
      trouves.push(chemin);
    }
  }
  return trouves;
}

describe('E1 — les actions révélées au survol le sont aussi au focus', () => {
  it('aucune grappe d’actions n’apparaît uniquement au survol', () => {
    const fautifs: string[] = [];

    for (const chemin of fichiersTsx(RACINE)) {
      const source = readFileSync(chemin, 'utf-8');
      // On ne juge que les conteneurs qui masquent quelque chose de cliquable.
      if (!source.includes('opacity-0 group-hover:opacity-100')) continue;
      // `<button>` natif OU composant `<Button>` : la relecture a relevé que
      // ne chercher que le premier laisserait passer une grappe d'actions bâtie
      // sur le composant maison. Les liens aussi sont focusables.
      if (!/<button|<Button|<a\s|role="button"/.test(source)) continue;

      const lignes = source.split('\n');
      lignes.forEach((ligne, index) => {
        if (
          ligne.includes('opacity-0 group-hover:opacity-100') &&
          !ligne.includes('group-focus-within:opacity-100')
        ) {
          fautifs.push(`${chemin.replace(RACINE, 'src')}:${index + 1}`);
        }
      });
    }

    expect(fautifs,
      'ces conteneurs masquent des contrôles focusables : au clavier, le focus ' +
      's’y pose sans que rien ne soit visible. Ajouter ' +
      '`group-focus-within:opacity-100` à côté de `group-hover:opacity-100`.\n' +
      fautifs.join('\n'),
    ).toEqual([]);
  });
});
