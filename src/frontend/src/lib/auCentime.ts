/**
 * B-1428 (décision du 25/09, RFC P-121 question 26) : arrondi commercial au
 * centime, demi-centime vers le haut en valeur absolue, identique au moteur
 * (`_au_centime`, Decimal ROUND_HALF_UP sur `repr`). `Math.round(x * 100)`
 * se trompait sur 1,005 (100,49999… en binaire) et divergeait du `round` de
 * Python sur 3,125. On arrondit la représentation décimale courte du nombre.
 */
export function auCentime(valeur: number): number {
  if (!Number.isFinite(valeur)) return valeur;
  const signe = valeur < 0 ? -1 : 1;
  const centimes = Math.round(Number(`${Math.abs(valeur)}e2`));
  return (signe * centimes) / 100 || 0;
}
