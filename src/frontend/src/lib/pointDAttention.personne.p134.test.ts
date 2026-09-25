/**
 * P-134 (persona Nathalie, cycle 13) : cliquer « Relancer Karim Benali » à
 * l'Accueil ouvrait la liste générale des tâches, ni la tâche ni la fiche de
 * Karim (donc pas son numéro). Un point qui nomme une personne ouvre sa fiche.
 */
import { describe, expect, it } from 'vitest';
import { buildTodayAttentionItems } from '../components/prototype/prototypeReadModels';
import { destinationDuPoint } from './pointDAttention';
import type { TodayDashboard } from '../services/api/dashboard';

function brief(partiel: Partial<TodayDashboard>): TodayDashboard {
  return {
    date: '2026-09-25', events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [], stale_prospects: [],
    indisponibles: [], summary: {} as TodayDashboard['summary'], ...partiel,
  };
}

describe('P-134 : « Relancer … » ouvre la personne', () => {
  it('une tâche reliée à un contact ouvre sa fiche', () => {
    const [point] = buildTodayAttentionItems(brief({
      urgent_tasks: [{ id: 't1', title: 'Relancer Karim Benali', status: 'todo', priority: 'medium', due_date: '2026-09-25T09:00:00', project_id: null, contact_id: 'c-karim' }],
    }));
    expect(destinationDuPoint(point)).toEqual({ kind: 'contact', id: 'c-karim' });
  });

  it('une tâche sans contact garde la liste des tâches', () => {
    const [point] = buildTodayAttentionItems(brief({
      urgent_tasks: [{ id: 't2', title: 'Ranger le bureau', status: 'todo', priority: 'medium', due_date: '2026-09-25T09:00:00', project_id: null, contact_id: null }],
    }));
    expect(destinationDuPoint(point)).toEqual({ kind: 'view', view: 'tasks' });
  });

  it('un prospect à relancer ouvre sa fiche', () => {
    const [point] = buildTodayAttentionItems(brief({
      stale_prospects: [{ id: 'c-nadia', name: 'Nadia Roux', company: null, stage: 'discovery', score: 60, last_interaction: null, next_follow_up: '2026-09-25T09:00:00' } as never],
    }));
    expect(destinationDuPoint(point)).toEqual({ kind: 'contact', id: 'c-nadia' });
  });
});
