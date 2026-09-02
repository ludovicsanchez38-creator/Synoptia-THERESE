/**
 * La ligne « Relancer X » doit dire POURQUOI elle est là (revue du 29/08).
 *
 * Le backend envoie désormais `next_follow_up`, la date que Ludo a décidée.
 * Sans elle à l'écran, le brief affiche un devoir sans sa justification, et
 * la définition a changé sans que rien ne le dise.
 */
import { describe, expect, it } from 'vitest';
import type { TodayDashboard } from '../../services/api/dashboard';
import { buildTodayAttentionItems } from './prototypeReadModels';

function journee(prospects: TodayDashboard['stale_prospects'], date = '2026-08-29'): TodayDashboard {
  return {
    date,
    events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [],
    stale_prospects: prospects,
    indisponibles: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: prospects.length },
  };
}

const BASE = { id: 'p1', name: 'Nicolas Ponzo', company: 'Mairie de Genas', stage: 'contact', email: null, last_interaction: null };

describe('La relance affichée dit sa date', () => {
  it('montre la date décidée, pas seulement le nom', () => {
    const [item] = buildTodayAttentionItems(journee([{ ...BASE, next_follow_up: '2026-03-15T00:00:00Z' }]));

    expect(item.title).toBe('Relancer Nicolas Ponzo');
    expect(item.detail).toContain('15/03');
  });

  it('marque comme urgente une relance échue', () => {
    const [item] = buildTodayAttentionItems(journee([{ ...BASE, next_follow_up: '2026-03-15T00:00:00Z' }]));

    // Le brief remonte les retards en tête et les badge. Une relance décidée
    // il y a cinq mois n'est pas un point de contexte parmi d'autres.
    expect(item.urgent).toBe(true);
  });

  it("n'invente pas de date quand il n'y en a pas", () => {
    const [item] = buildTodayAttentionItems(journee([{ ...BASE, next_follow_up: null }]));

    expect(item.detail).not.toMatch(/\d{2}\/\d{2}/);
    expect(item.urgent).toBe(false);
  });

  it('interprète un horodatage UTC selon le jour civil de Paris', () => {
    const [item] = buildTodayAttentionItems(journee(
      [{ ...BASE, next_follow_up: '2026-08-29T22:00:00Z' }],
      '2026-08-30',
    ));

    expect(item.detail).toContain('30/08');
    expect(item.urgent).toBe(false);
  });
});
