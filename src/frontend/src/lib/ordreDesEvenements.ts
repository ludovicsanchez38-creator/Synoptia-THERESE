import type { CalendarEvent } from '../services/api';

/** B-577 (05/09/2026) : journée entière d'abord, puis par heure de début. */
export function trierLesEvenementsDuJour(evenements: CalendarEvent[]): CalendarEvent[] {
  return [...evenements].sort((a, b) => {
    if (a.all_day !== b.all_day) return a.all_day ? -1 : 1;
    return (a.start_datetime ?? a.start_date ?? '').localeCompare(b.start_datetime ?? b.start_date ?? '');
  });
}
