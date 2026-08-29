/**
 * L'étanchéité du variateur (plan du 29/08/2026).
 *
 * Soso, sur ma proposition de « chercher la chaîne dans le prompt » :
 * « Chercher une chaîne dans un prompt est un détecteur de fumée, pas une
 * garantie. » Elle rate une reformulation, une valeur dérivée, un second tour
 * d'outil, et la fuite par le nombre d'éléments affichés.
 *
 * La propriété testée ici est la NON-INTERFÉRENCE : à message, historique et
 * données métier identiques, ce qui part vers le modèle est identique quelle
 * que soit la valeur du variateur. Elle tient par construction tant que la
 * valeur ne quitte jamais la projection React, et ces deux tests gardent cette
 * construction.
 *
 * Le jour où quelqu'un « alignerait » le chat sur le brief réduit, il y aurait
 * soit une fuite, soit un assistant qui ratifie des échéances invisibles.
 * Ce jour-là doit être bruyant, pas silencieux.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const RACINE = join(__dirname, '..');

/** Seuls ces fichiers ont le droit de connaître le variateur. */
const AUTORISES = new Set([
  'lib/variateurDuBrief.ts',
  'lib/variateurDuBrief.etancheite.test.ts',
  'components/prototype/TodayDashboardCard.tsx',
  'components/prototype/TodayDashboardCard.variateur.test.tsx',
]);

function fichiersSource(dossier: string, acc: string[] = []): string[] {
  for (const entree of readdirSync(dossier)) {
    if (entree === 'node_modules' || entree.startsWith('.')) continue;
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) fichiersSource(chemin, acc);
    else if (/\.tsx?$/.test(entree)) acc.push(chemin);
  }
  return acc;
}

describe('Étanchéité du variateur du brief', () => {
  it("n'est connu d'aucune couche qui parle au modèle ou au backend", () => {
    const coupables = fichiersSource(RACINE)
      .filter((chemin) => /variateurDuBrief/.test(readFileSync(chemin, 'utf-8')))
      .map((chemin) => relative(RACINE, chemin).split('\\').join('/'))
      .filter((chemin) => !AUTORISES.has(chemin));

    // Si ce test casse, la question n'est pas « comment le faire passer » :
    // c'est « pourquoi une valeur d'affichage traverse-t-elle cette couche ».
    expect(coupables).toEqual([]);
  });

  it("ne connaît lui-même ni le réseau, ni la mémoire, ni les outils", () => {
    const source = readFileSync(join(RACINE, 'lib/variateurDuBrief.ts'), 'utf-8');

    for (const interdit of ['fetch(', 'axios', 'services/api', 'stores/', 'invoke(']) {
      expect(source).not.toContain(interdit);
    }
  });
});
