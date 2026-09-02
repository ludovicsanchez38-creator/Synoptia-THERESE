/**
 * B-094 : trois composants d'interface que plus aucun écran ne monte.
 *
 * `GuidedPrompts` (565 lignes), `HomeHeader` et `CommandCategoryGroup`
 * n'avaient aucune référence hors de leur propre fichier, de leur baril et de
 * leurs tests. Ils compilaient, ils passaient le lint, ils se relisaient au
 * moindre refactor, et personne ne pouvait les voir : le baril les exporte,
 * l'export ressemble à un usage, et rien ne distingue un composant vivant d'un
 * composant que l'application a cessé d'afficher.
 *
 * Un baril n'est pas un appelant. Ce test compte les VRAIS importateurs des
 * composants de `home/` et `guided/` : le fichier lui-même, son baril et les
 * tests ne comptent pas.
 *
 * Deux mesures shell fausses avaient précédé la fiche de bug (le grep large
 * comptait les mentions du baril) : d'où un test qui exclut explicitement les
 * deux sources de faux positifs, plutôt qu'un décompte à la main.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join, basename } from 'node:path';

const ici = dirname(fileURLToPath(import.meta.url));
const racineSrc = resolve(ici, '../..');
const DOSSIERS_SURVEILLES = ['components/home', 'components/guided'];

function fichiers(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree === 'dist') continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) {
      fichiers(chemin, acc);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entree)) continue;
    acc.push(chemin);
  }
  return acc;
}

function estUnTest(chemin: string): boolean {
  return /\.(test|spec)\.(tsx|ts)$/.test(chemin);
}

function estUnBaril(chemin: string): boolean {
  return basename(chemin) === 'index.ts';
}

/** Les composants React exportés par un fichier `.tsx`. */
function composantsExportes(contenu: string): string[] {
  return [...contenu.matchAll(/^export function ([A-Z][A-Za-z0-9]*)/gm)].map(
    (m) => m[1],
  );
}

const tousLesFichiers = fichiers(racineSrc);

describe('B-094 - un composant livré est atteignable', () => {
  it('parcourt bien les dossiers surveillés', () => {
    const surveilles = tousLesFichiers.filter((f) =>
      DOSSIERS_SURVEILLES.some((d) => f.includes(d)),
    );
    expect(surveilles.length).toBeGreaterThan(15);
  });

  it('chaque composant de home/ et guided/ a au moins un écran qui le monte', () => {
    const orphelins: string[] = [];

    for (const fichier of tousLesFichiers) {
      if (!fichier.endsWith('.tsx')) continue;
      if (estUnTest(fichier)) continue;
      if (!DOSSIERS_SURVEILLES.some((d) => fichier.includes(d))) continue;

      for (const composant of composantsExportes(readFileSync(fichier, 'utf-8'))) {
        const motif = new RegExp(`(?<![A-Za-z0-9])${composant}(?![A-Za-z0-9])`);
        const appelants = tousLesFichiers.filter((autre) => {
          if (autre === fichier) return false;
          if (estUnTest(autre) || estUnBaril(autre)) return false;
          return motif.test(readFileSync(autre, 'utf-8'));
        });

        if (appelants.length === 0) {
          orphelins.push(
            `${composant} (${fichier.slice(racineSrc.length + 1)}) : aucun ` +
              `fichier hors de son baril et de ses tests ne le référence, ` +
              `donc aucun écran ne l'affiche`,
          );
        }
      }
    }

    expect(orphelins, orphelins.join('\n')).toEqual([]);
  });
});
