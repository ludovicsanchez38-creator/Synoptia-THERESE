import { describe, expect, it } from 'vitest';
import { getTimedEventLayout } from './calendarEventLayout';
import type { CalendarEvent } from '../../services/api';

function buildEvent(
  id: string,
  start: string,
  end: string
): CalendarEvent {
  return {
    id,
    calendar_id: 'cal-1',
    summary: id,
    description: null,
    location: null,
    start_datetime: start,
    end_datetime: end,
    start_date: null,
    end_date: null,
    all_day: false,
    attendees: null,
    recurrence: null,
    status: 'confirmed',
    synced_at: '2026-07-02T00:00:00',
  };
}

describe('getTimedEventLayout', () => {
  it('place deux événements au même créneau côte à côte', () => {
    const layouts = getTimedEventLayout(
      [
        buildEvent('evt-a', '2026-07-02T13:00:00', '2026-07-02T14:00:00'),
        buildEvent('evt-b', '2026-07-02T13:00:00', '2026-07-02T14:00:00'),
      ],
      8,
      20,
      60
    );

    expect(layouts['evt-a'].leftPercent).toBe(0);
    expect(layouts['evt-a'].widthPercent).toBe(50);
    expect(layouts['evt-b'].leftPercent).toBe(50);
    expect(layouts['evt-b'].widthPercent).toBe(50);
  });

  it('n empile pas deux événements simplement contigus', () => {
    const layouts = getTimedEventLayout(
      [
        buildEvent('evt-a', '2026-07-02T13:00:00', '2026-07-02T14:00:00'),
        buildEvent('evt-b', '2026-07-02T14:00:00', '2026-07-02T15:00:00'),
      ],
      8,
      20,
      60
    );

    expect(layouts['evt-a'].widthPercent).toBe(100);
    expect(layouts['evt-b'].widthPercent).toBe(100);
  });

  it('laisse un événement étendre sa largeur quand la colonne voisine est libre', () => {
    const layouts = getTimedEventLayout(
      [
        buildEvent('evt-a', '2026-07-02T09:00:00', '2026-07-02T12:00:00'),
        buildEvent('evt-b', '2026-07-02T09:00:00', '2026-07-02T10:00:00'),
        buildEvent('evt-c', '2026-07-02T10:00:00', '2026-07-02T11:00:00'),
      ],
      8,
      20,
      60
    );

    expect(layouts['evt-a'].widthPercent).toBe(50);
    expect(layouts['evt-b'].widthPercent).toBe(50);
    expect(layouts['evt-c'].widthPercent).toBe(50);
  });
  /**
   * B-058 : un rendez-vous à cheval sur minuit recevait `null` — les minutes
   * étaient comptées DANS LA JOURNÉE, donc la fin (01:00 = 60) tombait avant
   * le début (23:00 = 1380) et le garde `clampedStart >= clampedEnd` le
   * supprimait de la grille, même sur une grille 0h-24h.
   */
  it('borne à la fin de journée un événement dont la fin tombe le lendemain', () => {
    const layouts = getTimedEventLayout(
      [buildEvent('evt-nuit', '2026-07-02T23:00:00', '2026-07-03T01:00:00')],
      8,
      24,
      60
    );

    expect(layouts['evt-nuit']).toBeDefined();
    // 23:00 sur une grille qui commence à 8h : 15 heures plus bas.
    expect(layouts['evt-nuit'].top).toBe(15 * 60);
    // Bornée à 24:00, il reste une heure de hauteur.
    expect(layouts['evt-nuit'].height).toBe(60);
  });

  it('traite une fin à minuit pile comme la fin de la journée', () => {
    const layouts = getTimedEventLayout(
      [buildEvent('evt-minuit', '2026-07-02T22:30:00', '2026-07-03T00:00:00')],
      8,
      24,
      60
    );

    expect(layouts['evt-minuit']).toBeDefined();
    expect(layouts['evt-minuit'].height).toBe(90);
  });

  it('laisse intact un événement qui finit le jour même', () => {
    const layouts = getTimedEventLayout(
      [buildEvent('evt-jour', '2026-07-02T09:00:00', '2026-07-02T10:00:00')],
      8,
      20,
      60
    );

    expect(layouts['evt-jour'].top).toBe(60);
    expect(layouts['evt-jour'].height).toBe(60);
  });
});
