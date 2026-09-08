/** P-048 (revue COCO, finding 4) : une échéance du jour apparaissait déjà en retard (minuit < maintenant). */
import { describe, expect, it } from 'vitest';

import { estEnRetard } from './livrables';

const maintenant = new Date(2026, 8, 8, 15, 30); // 8 septembre 2026, 15 h 30, heure locale

describe('estEnRetard (P-048)', () => {
  it('hier : en retard', () => {
    expect(estEnRetard({ due_date: '2026-09-07T00:00:00', status: 'en_cours' }, maintenant)).toBe(true);
  });
  it('aujourd’hui : pas en retard, même l’après-midi', () => {
    expect(estEnRetard({ due_date: '2026-09-08T00:00:00', status: 'en_cours' }, maintenant)).toBe(false);
  });
  it('demain : pas en retard', () => {
    expect(estEnRetard({ due_date: '2026-09-09T00:00:00', status: 'a_faire' }, maintenant)).toBe(false);
  });
  it('validé ou sans échéance : jamais en retard', () => {
    expect(estEnRetard({ due_date: '2026-09-01T00:00:00', status: 'valide' }, maintenant)).toBe(false);
    expect(estEnRetard({ due_date: null, status: 'en_cours' }, maintenant)).toBe(false);
  });
});
