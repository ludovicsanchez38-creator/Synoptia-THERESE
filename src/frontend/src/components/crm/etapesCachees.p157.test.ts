/**
 * P-157 : à cadre étroit, la grille des huit étapes défile et les colonnes
 * suivantes existent sans que rien le dise. Le décompte, la mention et le
 * défilement vers la première étape cachée sont purs (pas de DOM).
 */
import { describe, expect, it } from 'vitest';

import {
  decompteEtapesCachees,
  defilementVersEtapesCachees,
  mentionDEtapesCachees,
  type MesureColonne,
} from './etapesCachees';

/** 15 rem = 240 px, gouttière `gap-3` = 12 px. */
function colonnesPipeline(nombre = 8, largeur = 240, pas = 252): MesureColonne[] {
  return Array.from({ length: nombre }, (_, index) => ({ gauche: index * pas, largeur }));
}

describe('P-157 : étapes hors cadre', () => {
  it('à 800 px, cinq des huit colonnes restent à droite', () => {
    expect(decompteEtapesCachees({ scrollLeft: 0, clientWidth: 800 }, colonnesPipeline())).toEqual({
      aGauche: 0,
      aDroite: 5,
    });
  });

  it('après défilement, compte les deux côtés', () => {
    expect(decompteEtapesCachees({ scrollLeft: 756, clientWidth: 800 }, colonnesPipeline())).toEqual({
      aGauche: 3,
      aDroite: 2,
    });
  });

  it('ne compte rien quand le cadre contient toutes les colonnes', () => {
    expect(decompteEtapesCachees({ scrollLeft: 0, clientWidth: 2100 }, colonnesPipeline())).toEqual({
      aGauche: 0,
      aDroite: 0,
    });
  });

  it('ignore un dépassement d’un pixel (sous-pixel de rendu)', () => {
    const colonne = [{ gauche: 0, largeur: 241 }];
    expect(decompteEtapesCachees({ scrollLeft: 0, clientWidth: 240 }, colonne)).toEqual({
      aGauche: 0,
      aDroite: 0,
    });
    expect(decompteEtapesCachees({ scrollLeft: 0, clientWidth: 240 }, [{ gauche: 0, largeur: 242 }])).toEqual({
      aGauche: 0,
      aDroite: 1,
    });
  });

  it('une colonne plus large que le cadre compte des deux côtés', () => {
    expect(decompteEtapesCachees(
      { scrollLeft: 100, clientWidth: 400 },
      [{ gauche: 0, largeur: 1000 }],
    )).toEqual({ aGauche: 1, aDroite: 1 });
  });

  it('accorde la mention, au singulier comme au pluriel', () => {
    expect(mentionDEtapesCachees(1, 'droite')).toBe('1 étape à droite');
    expect(mentionDEtapesCachees(3, 'gauche')).toBe('3 étapes à gauche');
    expect(mentionDEtapesCachees(5, 'droite')).toBe('5 étapes à droite');
  });

  it('vise la première colonne encore cachée du côté demandé', () => {
    const colonnes = colonnesPipeline();
    expect(defilementVersEtapesCachees({ scrollLeft: 0, clientWidth: 800 }, colonnes, 'droite')).toBe(756);
    expect(defilementVersEtapesCachees({ scrollLeft: 756, clientWidth: 800 }, colonnes, 'gauche')).toBe(504);
    expect(defilementVersEtapesCachees({ scrollLeft: 0, clientWidth: 2100 }, colonnes, 'droite')).toBeNull();
  });

  it('avance quand la première colonne dépasse déjà la largeur du cadre', () => {
    const vue = { scrollLeft: 0, clientWidth: 200 };
    const colonnes = [
      { gauche: 0, largeur: 240 },
      { gauche: 252, largeur: 240 },
    ];
    // 240 - 200 : amener le bout caché de la colonne dans le cadre, pas rester à 0.
    expect(defilementVersEtapesCachees(vue, colonnes, 'droite')).toBe(40);
  });
});
