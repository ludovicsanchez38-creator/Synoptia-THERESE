/**
 * Cycle 6, lecteur #124 (CalendarPanel.tsx) : le message actionnable posé par
 * `loadCalendars` (API Google Calendar à activer) était effacé aussitôt : avec
 * du cache, `calendarsReady` passait vrai, `loadEvents` partait et commençait
 * par `setError(null)`. Un succès sur l'agenda local faisait disparaître
 * l'explication sans geste de l'utilisateur.
 */
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const { CAUSE } = vi.hoisted(() => ({ CAUSE: 'Google Calendar API has not been used in project 42 before or it is disabled.' }));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: true, accounts: [] }),
    listCalendars: vi.fn().mockRejectedValue(new Error(CAUSE)),
    listEvents: vi.fn().mockResolvedValue([]),
  };
});

import { CalendarPanel } from './CalendarPanel';

describe('#124 : l’explication d’un 403 Google survit au chargement des événements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalendarStore.setState({
      calendars: [{ id: 'loc', provider: 'local', summary: 'Mon calendrier', primary: true }] as never,
      currentCalendarId: 'loc', events: [], currentEventId: null, isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
  });

  it('le message reste affiché après un chargement d’événements réussi sur le cache', async () => {
    render(<CalendarPanel standalone />);
    for (let tour = 0; tour < 6; tour++) {
      await act(async () => { await Promise.resolve(); });
    }
    expect(screen.getByText(new RegExp(CAUSE.slice(0, 40)))).toBeInTheDocument();
  });
});
