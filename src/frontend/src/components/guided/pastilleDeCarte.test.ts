/**
 * 01/09/2026 - Les pastilles des cartes d'action peignaient avec des jetons
 * retirés de la charte.
 *
 * `ActionCard` construisait `var(--k1)` à `var(--k4)` et leurs variantes de
 * fond À L'EXÉCUTION. Ces jetons ont zéro définition dans `globals.css`, dont
 * le commentaire dit qu'ils ont été remplacés par les jetons de domaine. Les
 * pastilles n'avaient donc ni fond ni couleur d'icône.
 *
 * L'audit graphique des 0.60 et 0.61 l'avait manqué parce qu'un nom assemblé
 * à l'exécution est invisible à une recherche de texte.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { jetonDePastille, JETONS_DE_PASTILLE } from './pastilleDeCarte';

const charte = readFileSync(join(process.cwd(), 'src/styles/globals.css'), 'utf-8');

describe('pastille des cartes d’action', () => {
  it('n’emploie que des jetons définis dans la charte', () => {
    for (const jeton of JETONS_DE_PASTILLE) {
      expect(charte, `${jeton} absent de globals.css`).toContain(`${jeton}:`);
    }
  });

  it('donne un jeton stable pour chaque position, et quatre teintes distinctes', () => {
    // La fonction rend un objet neuf a chaque appel : on compare les valeurs,
    // pas les identites.
    const teintes = [0, 1, 2, 3, 4].map((i) => jetonDePastille(i).teinte);
    expect(teintes[4]).toBe(teintes[0]);
    expect(new Set(teintes.slice(0, 4)).size).toBe(4);
  });

  it('ne référence plus les anciens jetons retirés', () => {
    for (let i = 0; i < 8; i += 1) {
      expect(jetonDePastille(i).teinte).not.toMatch(/--k\d/);
    }
  });
});
