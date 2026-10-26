import { auCentime } from './auCentime';

/** B-1165 : HT au centime par ligne, puis TVA au centime sur la base de chaque taux. */
export function invoiceTotals(lines: { totalHT: number; tvaRate: number }[]) {
  const bases = new Map<number, number>();
  let subtotalHT = 0;
  for (const { totalHT, tvaRate } of lines) {
    const centimes = Math.round(totalHT * 100);
    bases.set(tvaRate, (bases.get(tvaRate) ?? 0) + centimes);
    subtotalHT += centimes;
  }
  let taxeCentimes = 0;
  for (const [taux, base] of bases) {
    taxeCentimes += Math.round(auCentime(base * taux / 10000) * 100);
  }
  return {
    subtotalHT: subtotalHT / 100,
    totalTax: taxeCentimes / 100,
    totalTTC: (subtotalHT + taxeCentimes) / 100,
  };
}
