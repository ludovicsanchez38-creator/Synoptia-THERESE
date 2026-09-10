/** Lot 2 DA : la ligne du jour de l'Accueil (date française, sources, heure). */
import { describe, expect, it } from 'vitest';

import type { TodayDashboard } from '../../services/api/dashboard';
import { formaterLeJour, ligneDuJour } from './ligneDuJour';

const brief = (overrides: Partial<TodayDashboard> = {}): TodayDashboard => ({
  date: '2026-09-10', events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [], stale_prospects: [], indisponibles: [],
  summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
  ...overrides,
});

describe('formaterLeJour', () => {
  it('écrit la date en français, premier caractère seul en capitale, sans décalage de fuseau', () => {
    expect(formaterLeJour('2026-09-10')).toBe('Jeudi 10 septembre');
    expect(formaterLeJour('2026-01-01')).toBe('Jeudi 1 janvier');
    expect(formaterLeJour('pas une date')).toBeNull();
  });
});

describe('ligneDuJour', () => {
  it('sans ressource : l’heure seule ; avec ressource : date, sources présentes en minuscules (CRM reste un sigle), heure', () => {
    expect(ligneDuJour(null, '21:40')).toBe('Rafraîchi à 21:40');
    expect(ligneDuJour(brief(), '21:40')).toBe('Jeudi 10 septembre · Rafraîchi à 21:40');
    const data = brief({
      urgent_tasks: [{ id: 't', title: 'T', status: 'todo', priority: 'high', due_date: null, project_id: null }],
      stale_prospects: [{ id: 'p', name: 'P', company: null, stage: 'lead', email: null, last_interaction: null, next_follow_up: null }],
      indisponibles: ['calendrier'],
    });
    expect(ligneDuJour(data, '21:40')).toBe('Jeudi 10 septembre · Sources : tâches, CRM · Rafraîchi à 21:40');
    expect(ligneDuJour(data, null)).toBe('Jeudi 10 septembre · Sources : tâches, CRM');
  });
});
