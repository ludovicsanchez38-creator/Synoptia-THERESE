/**
 * DA « Application affinée », lot 6 : gardes de source sur les SIX fichiers
 * de l'écran Projets et tâches
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, décision 5).
 *
 * Le geste de l'écran est à 36 px : plus aucun `Button size="sm"` (32 px,
 * `Button.tsx` `size === 'sm' && 'h-8 …'`). La garde d'origine ne lisait que
 * `TasksPanel.tsx` et `ProjectsPanel.tsx` : un `size="sm"` revenu dans
 * `TaskKanban`, `TaskList`, `TaskForm` ou `ProjectsKanban` serait passé sans
 * un mot. Une seule garde, les six fichiers.
 */
import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

import { CHEMINS_LOT6, FICHIERS_LOT6 } from './fichiersLot6';

function lignes(chemin: string, motif: RegExp): number[] {
  return readFileSync(chemin, 'utf-8')
    .split('\n')
    .map((ligne, i) => (motif.test(ligne) ? i + 1 : 0))
    .filter((n) => n > 0);
}

describe('lot 6 DA - les six fichiers de l’écran Projets et tâches', () => {
  it('aucun Button size="sm" : le geste de l’écran est à 36 px', () => {
    const fautifs = CHEMINS_LOT6
      .map((chemin, i) => ({ nom: FICHIERS_LOT6[i], ou: lignes(chemin, /size="sm"/) }))
      .filter((f) => f.ou.length > 0)
      .map((f) => `${f.nom}:${f.ou.join(',')}`);

    expect(fautifs, `${fautifs.length} fichier(s) sous le geste de 36 px`).toEqual([]);
  });
});
