/** B-1428 : l'écran arrondit comme le moteur (demi-centime vers le haut, en
 *  valeur absolue), sur la représentation décimale courte du nombre. */
import { describe, expect, it } from 'vitest';

import { auCentime } from './auCentime';

describe('B-1428 : arrondi commercial au centime', () => {
  it.each([
    [2.5 * 1.25, 3.13],
    [1.005, 1.01],
    [2.675, 2.68],
    [-3.125, -3.13],
    [1000.005, 1000.01],
    [0.1 * 3, 0.3],
    [99.99, 99.99],
  ])('%s → %s', (valeur, attendu) => {
    expect(auCentime(valeur)).toBe(attendu);
  });
});
