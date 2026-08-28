/**
 * E3 — le titre d'une surface doit suivre le verbe qui l'ouvre.
 *
 * Campagne dix personas, constat U3 : après un clic sur **Écrire**, trois
 * libellés parlaient de LECTURE. `scenarioLabels[scenario]` n'est pas
 * décoratif — c'est le titre accessible du canevas : un utilisateur au lecteur
 * d'écran cliquait **Écrire** et s'entendait annoncer **« Consulter mes
 * emails »**.
 *
 * La dérive vient de la v0.53.0 : l'entrée 10 a changé ce que le verbe FAIT,
 * les titres sont restés. `lexiqueTitres.test.ts` ne les couvrait pas.
 *
 * Un premier jet de ce gate posait une liste de mots interdits (« consulter »,
 * « lecture »). La relecture l'a rejeté, à raison : il forçait à renommer la
 * boîte de réception, qui EST une consultation, et cassait au hasard des mots
 * sur les autres verbes. Le gate appariE désormais deux tables voisines —
 * rigide sur cinq paires, ce qui est le bon grain : la prochaine entrée qui
 * change un comportement devra toucher la table, sinon ce test tombe.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { ACTIONS_ETABLI, TITRES_ETABLI } from './etabli';

describe('E3 — chaque verbe de l’établi porte le titre de sa surface', () => {
  it('les cinq verbes ont un titre, et rien d’autre n’en a', () => {
    const verbes = ACTIONS_ETABLI.map((a) => a.id).sort();
    expect(Object.keys(TITRES_ETABLI).sort()).toEqual(verbes);
  });

  it('le titre de « Écrire » annonce une écriture', () => {
    // Le cas qui a dérivé : « Écrire » → « Consulter mes emails ».
    expect(TITRES_ETABLI.email).toMatch(/écrire|rédiger|message/i);
  });

  it('la coque affiche ces titres, elle n’en tient pas une copie', () => {
    // La dérive était rendue possible par la duplication : la coque avait sa
    // propre table, loin des verbes. Elle doit consommer celle-ci.
    const coque = readFileSync(
      join(__dirname, '..', 'components', 'prototype', 'ConversationCanvasPrototype.tsx'),
      'utf-8',
    );
    expect(coque).toContain('TITRES_ETABLI');
  });
});
