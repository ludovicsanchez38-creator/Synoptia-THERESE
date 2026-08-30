/**
 * Lot 3 du plan de cohérence graphique (30/08/2026) : un rayon unique.
 *
 * Trois systèmes cohabitaient : la DA (14 px), les jetons du code
 * (6/8/12/16 px) et 494 valeurs écrites à la main, presque toujours à un
 * pixel du jeton (9 au lieu de 8, 13 au lieu de 12, 7 au lieu de 6). Avec les
 * classes nommées, l'application portait 26 rayons différents.
 *
 * Trois suffisent : petit (champs, puces), moyen (boutons, cartes), plein
 * (étiquettes).
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = resolve(process.cwd(), 'src');
const CSS = readFileSync(join(RACINE, 'styles/globals.css'), 'utf-8');

const SOURCES: string[] = [];
(function collecter(dossier: string) {
  for (const e of readdirSync(dossier, { withFileTypes: true })) {
    const chemin = join(dossier, e.name);
    if (e.isDirectory()) collecter(chemin);
    else if (/\.tsx?$/.test(e.name) && !/\.test\.tsx?$/.test(e.name)) SOURCES.push(chemin);
  }
})(RACINE);

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);
const AUTORISES = new Set(['sm', 'md', 'full']);

describe('lot 3 : trois rayons, pas vingt-six', () => {
  it('aucun rayon n’est écrit en pixels dans les composants', () => {
    const fautifs: string[] = [];
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(
        /\brounded(?:-[a-z]{1,2})?-\[[^\]]+\]/g,
      )) {
        fautifs.push(`${court(f)} : ${m[0]}`);
      }
    }
    expect(fautifs, `${fautifs.length} rayons manuels, ex. ${fautifs.slice(0, 3).join(' | ')}`).toEqual(
      [],
    );
  });

  it('seules trois tailles de rayon sont employées', () => {
    const vues = new Map<string, number>();
    for (const f of SOURCES) {
      for (const m of readFileSync(f, 'utf-8').matchAll(
        /\brounded(?:-[a-z]{1,2})?-(none|sm|md|lg|xl|2xl|3xl|full)\b/g,
      )) {
        vues.set(m[1], (vues.get(m[1]) ?? 0) + 1);
      }
    }
    const interdites = [...vues.entries()].filter(([t]) => !AUTORISES.has(t));
    expect(
      interdites.map(([t, n]) => `${t} (${n})`),
      'tailles hors du jeu autorisé',
    ).toEqual([]);
  });

  it('aucun « rounded » nu ne subsiste', () => {
    // `rounded` seul vaut 4 px chez Tailwind : une quatrième valeur muette.
    const fautifs = SOURCES.filter((f) => /\brounded\b(?!-)/.test(readFileSync(f, 'utf-8')));
    expect(fautifs.map(court).slice(0, 5), `${fautifs.length} fichiers`).toEqual([]);
  });

  it('le jeu de jetons ne définit plus que deux tailles', () => {
    const jetons = [...CSS.matchAll(/--radius-([a-z0-9]+):\s*([^;]+);/g)].map(
      ([, nom, valeur]) => `${nom}:${valeur.trim()}`,
    );
    expect(jetons.sort()).toEqual(['md:0.875rem', 'sm:0.5rem']);
  });
  it('le CSS lui-même ne pose pas de rayon en dur', () => {
    // Le lot 3 ne balayait que les composants. body et #root gardaient 12 px
    // pendant que cartes et panneaux passaient à 14 : sur une fenêtre Tauri
    // transparente, le contour extérieur ne suivait pas.
    const AUTORISES = new Set(['4px', '999px', '50%']); // ascenseur, pastilles
    const fautifs: string[] = [];
    for (const m of CSS.matchAll(/border-radius:\s*([^;]+);/g)) {
      const valeur = m[1].trim();
      if (valeur.startsWith('var(--radius-')) continue;
      if (AUTORISES.has(valeur)) continue;
      fautifs.push(valeur);
    }
    expect(fautifs, `rayons en dur dans globals.css : ${fautifs.join(', ')}`).toEqual([]);
  });
});
