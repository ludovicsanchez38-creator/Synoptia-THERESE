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
});
