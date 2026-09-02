/**
 * B-058 : un rendez-vous à cheval sur minuit (23:00 -> 01:00) disparaissait de
 * l'agenda.
 *
 * Deux calculs, le même oubli : les minutes se comptaient DANS LA JOURNÉE, si
 * bien qu'une fin le lendemain retombait avant le début (1380 -> 60).
 * `getPositionedEvent` renvoyait donc `null` (garde `clampedStart >=
 * clampedEnd`) et `getVisibleHourRange` n'élargissait même pas la grille
 * jusqu'à 23 h. Le test passe par la vue rendue : corriger un seul des deux
 * laisse l'événement invisible, donc le test rouge.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { CalendarView } from './CalendarView';

function evenement(id: string, resume: string, debut: string, fin: string) {
  return {
    id,
    calendar_id: 'cal-1',
    summary: resume,
    description: null,
    location: null,
    start_datetime: debut,
    end_datetime: fin,
    start_date: null,
    end_date: null,
    all_day: false,
    attendees: null,
    recurrence: null,
    status: 'confirmed',
    synced_at: null,
  } as never;
}

describe('B-058 : un rendez-vous à cheval sur minuit reste dans la grille', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      // Jeudi 3 septembre 2026, dans la semaine du 31 août.
      selectedDate: new Date(2026, 8, 3),
      viewMode: 'week',
      showCancelled: false,
      searchQuery: '',
      currentEventId: null,
      isEventFormOpen: false,
      events: [
        evenement('evt-temoin', 'Témoin du matin', '2026-09-03T09:00:00', '2026-09-03T10:00:00'),
        evenement('evt-minuit', 'Garde de nuit', '2026-09-03T23:00:00', '2026-09-04T01:00:00'),
      ],
    });
  });

  it('la vue Semaine affiche le rendez-vous de nuit comme le témoin du matin', () => {
    render(<CalendarView />);

    expect(screen.getByText('Témoin du matin')).toBeInTheDocument();
    expect(screen.getByText('Garde de nuit')).toBeInTheDocument();
  });

  it('la vue Jour affiche aussi le rendez-vous de nuit', () => {
    useCalendarStore.setState({ viewMode: 'day' });
    render(<CalendarView />);

    expect(screen.getByText('Témoin du matin')).toBeInTheDocument();
    expect(screen.getByText('Garde de nuit')).toBeInTheDocument();
  });
});
