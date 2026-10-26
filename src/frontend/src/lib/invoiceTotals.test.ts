import { describe, expect, it } from 'vitest';
import { invoiceTotals } from './invoiceTotals';

describe('B-1165 : TVA calculée sur la base par taux', () => {
  it.each([
    [10, 12.34, 5.5, 123.4, 6.79, 130.19],
    [12, 0.99, 20, 11.88, 2.38, 14.26],
    [3, 33.33, 20, 99.99, 20, 119.99],
    [2, 2.5, 2.1, 5, 0.11, 5.11],
  ])('%s lignes de %s à %s %%', (nombre, totalHT, tvaRate, subtotalHT, totalTax, totalTTC) => {
    expect(invoiceTotals(Array.from({ length: nombre }, () => ({ totalHT, tvaRate }))))
      .toEqual({ subtotalHT, totalTax, totalTTC });
  });

  it('additionne les taxes de deux taux, indépendamment de l’ordre des lignes', () => {
    const lignes = [
      ...Array.from({ length: 10 }, () => ({ totalHT: 12.34, tvaRate: 5.5 })),
      ...Array.from({ length: 12 }, () => ({ totalHT: 0.99, tvaRate: 20 })),
    ];
    const attendu = { subtotalHT: 135.28, totalTax: 9.17, totalTTC: 144.45 };
    expect(invoiceTotals(lignes)).toEqual(attendu);
    expect(invoiceTotals(lignes.reverse())).toEqual(attendu);
  });
});
