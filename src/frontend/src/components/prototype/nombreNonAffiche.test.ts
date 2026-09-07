/**
 * B-425 (cycle 4) : le brief plafonne chaque liste à 50 côté serveur et
 * annonce le total réel ; l'écran dit combien manquent au lieu de se taire.
 */
import { describe, expect, it } from 'vitest';

import { nombreNonAffiche } from './prototypeReadModels';

const resume = (s: Record<string, number | undefined>) =>
  ({ summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0, ...s } }) as never;

describe('nombreNonAffiche', () => {
  it('vaut 0 quand tout est affiché ou quand le serveur ne dit pas de total', () => {
    expect(nombreNonAffiche(resume({ tasks_count: 3, tasks_total: 3 }))).toBe(0);
    expect(nombreNonAffiche(resume({ tasks_count: 3 }))).toBe(0);
    expect(nombreNonAffiche(null)).toBe(0);
  });

  it('additionne ce que chaque liste plafonnée a laissé de côté', () => {
    expect(nombreNonAffiche(resume({ tasks_count: 50, tasks_total: 60, follow_ups_count: 50, follow_ups_total: 52, invoices_count: 2, invoices_total: 2 }))).toBe(12);
  });
});
