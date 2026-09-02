/**
 * B-144 : en vue Semaine, l'événement du DERNIER jour affiché disparaissait.
 *
 * Le filtre de semaine parsait la clé civile « YYYY-MM-DD » avec `new Date()`,
 * donc à MINUIT UTC, puis la comparait à des bornes construites à minuit
 * LOCAL. À Paris (UTC+1/+2), minuit UTC du dimanche tombe deux heures après
 * minuit local du dimanche : la borne haute était franchie et la colonne du
 * dimanche se rendait vide. En UTC- c'est le premier jour qui saute ; en UTC
 * exactement, rien ne saute — d'où le fuseau forcé ici, sinon le test serait
 * vert sans rien prouver sur une machine en UTC.
 */
import { render, screen } from '@testing-library/react';
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { CalendarView } from './CalendarView';

function evenement(id: string, resume: string, jour: string) {
  return {
    id,
    calendar_id: 'cal-1',
    summary: resume,
    description: null,
    location: null,
    start_datetime: `${jour}T09:00:00`,
    end_datetime: `${jour}T10:00:00`,
    start_date: null,
    end_date: null,
    all_day: false,
    attendees: null,
    recurrence: null,
    status: 'confirmed',
    synced_at: null,
  } as never;
}

describe('B-144 : la semaine garde son dernier jour', () => {
  beforeAll(() => {
    vi.stubEnv('TZ', 'Europe/Paris');
  });

  afterAll(() => {
    vi.unstubAllEnvs();
  });

  beforeEach(() => {
    useCalendarStore.setState({
      // Mercredi 2 septembre 2026 : semaine du lundi 31 août au dimanche 6.
      selectedDate: new Date(2026, 8, 2),
      viewMode: 'week',
      showCancelled: false,
      searchQuery: '',
      currentEventId: null,
      isEventFormOpen: false,
      events: [
        evenement('evt-lundi', 'Témoin du lundi', '2026-08-31'),
        evenement('evt-dimanche', 'RDV du dimanche', '2026-09-06'),
        evenement('evt-hors', 'Lundi suivant', '2026-09-07'),
      ],
    });
  });

  it('le fuseau du test est bien un UTC+ (sinon le défaut est invisible)', () => {
    // Été à Paris : UTC+2, donc un décalage de -120 minutes.
    expect(new Date(2026, 8, 6).getTimezoneOffset()).toBe(-120);
  });

  it('un événement du dimanche affiché reste dans la grille Semaine', () => {
    render(<CalendarView />);

    expect(screen.getByText('Témoin du lundi')).toBeInTheDocument();
    expect(screen.getByText('RDV du dimanche')).toBeInTheDocument();
    // Contre-épreuve : la semaine suivante reste dehors.
    expect(screen.queryByText('Lundi suivant')).toBeNull();
  });
});
