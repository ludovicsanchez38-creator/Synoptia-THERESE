/**
 * Revue Grok du diff 0.70.0 (P2) : #124 garde le message d'un 403 Google quand
 * les événements se chargent sur le cache local ; mais un chargement réussi
 * DEPUIS GOOGLE prouve que l'API répond : le message devenu faux doit tomber,
 * avec le geste de reconnexion.
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

describe('Grok 0.70.0 P2 : un succès Google efface le message d’agendas devenu faux', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetch).mockImplementation(async () => new Response(
      JSON.stringify(reponseGoogle403.body), { status: reponseGoogle403.status },
    ));
    useCalendarStore.setState({
      calendars: [{ id: 'g1', provider: 'google', account_id: 'a1', summary: 'Ludo', primary: true }] as never,
      currentCalendarId: 'g1', events: [], currentEventId: null, isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [{ id: 'a1', email: 'ludo@example.fr', provider: 'gmail' }] as never, currentAccountId: 'a1', needsReauth: false });
  });

  it('le message du 403 disparaît quand les événements Google se chargent', async () => {
    let terminer: (evenements: api.CalendarEvent[]) => void = () => {};
    vi.mocked(api.listEvents).mockReturnValue(new Promise((resolve) => { terminer = resolve; }));
    render(<CalendarPanel standalone />);
    expect(await screen.findByText(reponseGoogle403.body.message)).toBeInTheDocument();
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    await act(async () => { terminer([]); });
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByText(reponseGoogle403.body.message)).toBeNull();
  });
});
