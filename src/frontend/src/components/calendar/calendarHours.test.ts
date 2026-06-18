import { describe, it, expect } from 'vitest';
import { getVisibleHourRange } from './calendarHours';

// Datetimes SANS suffixe Z => interprétés en heure locale => getHours() déterministe
// quelle que soit la timezone du runner CI.

describe('getVisibleHourRange', () => {
  it('retourne la plage par défaut quand il n y a aucun événement', () => {
    expect(getVisibleHourRange([], 8, 20)).toEqual({ startHour: 8, endHour: 20 });
  });

  it('garde la plage par défaut pour un événement déjà dans la fenêtre', () => {
    const events = [{ start_datetime: '2026-06-18T10:00:00', end_datetime: '2026-06-18T11:00:00' }];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 8, endHour: 20 });
  });

  it('élargit le début pour un événement tôt le matin (RDV à 7h ne doit plus disparaître)', () => {
    const events = [{ start_datetime: '2026-06-18T07:00:00', end_datetime: '2026-06-18T07:30:00' }];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 7, endHour: 20 });
  });

  it('élargit la fin pour un événement tardif (arrondi à l heure supérieure)', () => {
    const events = [{ start_datetime: '2026-06-18T21:00:00', end_datetime: '2026-06-18T22:30:00' }];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 8, endHour: 23 });
  });

  it('élargit des deux côtés avec plusieurs événements', () => {
    const events = [
      { start_datetime: '2026-06-18T06:15:00', end_datetime: '2026-06-18T07:00:00' },
      { start_datetime: '2026-06-18T10:00:00', end_datetime: '2026-06-18T11:00:00' },
      { start_datetime: '2026-06-18T20:00:00', end_datetime: '2026-06-18T21:00:00' },
    ];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 6, endHour: 21 });
  });

  it('ignore les événements journée entière (all_day)', () => {
    const events = [{ all_day: true, start_date: '2026-06-18' }];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 8, endHour: 20 });
  });

  it('ignore les événements sans datetime de début ou de fin', () => {
    const events = [{ start_datetime: '2026-06-18T07:00:00' }];
    expect(getVisibleHourRange(events, 8, 20)).toEqual({ startHour: 8, endHour: 20 });
  });

  it('ne dépasse jamais 0h-24h', () => {
    const events = [{ start_datetime: '2026-06-18T00:00:00', end_datetime: '2026-06-18T23:59:00' }];
    const r = getVisibleHourRange(events, 8, 20);
    expect(r.startHour).toBe(0);
    expect(r.endHour).toBe(24);
  });
});
