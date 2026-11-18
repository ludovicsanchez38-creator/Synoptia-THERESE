/**
 * Cycle 6, lecteur #124 (CalendarPanel.tsx) : le message actionnable posé par
 * `loadCalendars` (API Google Calendar à activer) était effacé aussitôt : avec
 * du cache, `calendarsReady` passait vrai, `loadEvents` partait et commençait
 * par `setError(null)`. Un succès sur l'agenda local faisait disparaître
 * l'explication sans geste de l'utilisateur.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import reponseGoogle403 from './fixtures/googleCalendar403.json';
import * as api from '../../services/api';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: true, accounts: [] }),
    listEvents: vi.fn().mockResolvedValue([]),
  };
});

import { CalendarPanel } from './CalendarPanel';

describe('#124 : l’explication d’un 403 Google survit au chargement des événements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetch).mockImplementation(async () => new Response(
      JSON.stringify(reponseGoogle403.body), { status: reponseGoogle403.status },
    ));
    useCalendarStore.setState({
      calendars: [{ id: 'loc', provider: 'local', summary: 'Mon calendrier', primary: true }] as never,
      currentCalendarId: 'loc', events: [], currentEventId: null, isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
  });

  it('le message reste affiché après un chargement d’événements réussi sur le cache', async () => {
    let terminer: (evenements: api.CalendarEvent[]) => void = () => {};
    vi.mocked(api.listEvents).mockReturnValue(new Promise((resolve) => { terminer = resolve; }));
    render(<CalendarPanel standalone />);
    expect(await screen.findByText(reponseGoogle403.body.message)).toBeInTheDocument();
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    await act(async () => { terminer([]); });
    expect(screen.getByText(reponseGoogle403.body.message)).toBeInTheDocument();
  });
});
