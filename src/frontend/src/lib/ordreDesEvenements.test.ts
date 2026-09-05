/**
 * B-577 (05/09/2026) : la vue Mois affichait les événements d'un jour dans
 * l'ordre reçu de l'API, pas dans l'ordre des heures.
 */
import { describe, expect, it } from 'vitest';
import type { CalendarEvent } from '../services/api';
import { trierLesEvenementsDuJour } from './ordreDesEvenements';

const evt = (id: string, extra: Partial<CalendarEvent>): CalendarEvent => ({
  id, calendar_id: 'c', summary: id, description: null, location: null, start_datetime: null, end_datetime: null,
  start_date: null, end_date: null, all_day: false, attendees: null, recurrence: null, status: 'confirmed', synced_at: '2026-09-05T00:00:00Z', ...extra,
});

describe('trierLesEvenementsDuJour (B-577)', () => {
  it('journée entière d’abord, puis par heure de début', () => {
    const tries = trierLesEvenementsDuJour([
      evt('soir', { start_datetime: '2026-09-10T18:00:00' }),
      evt('matin', { start_datetime: '2026-09-10T09:00:00' }),
      evt('journee', { all_day: true, start_date: '2026-09-10' }),
      evt('midi', { start_datetime: '2026-09-10T12:30:00' }),
    ]);
    expect(tries.map((e) => e.id)).toEqual(['journee', 'matin', 'midi', 'soir']);
  });
});
