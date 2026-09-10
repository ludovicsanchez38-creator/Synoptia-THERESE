/**
 * Revue Grok du diff 0.70.0 (P2) : #124 garde le message d'un 403 Google quand
 * les événements se chargent sur le cache local ; mais un chargement réussi
 * DEPUIS GOOGLE prouve que l'API répond : le message devenu faux doit tomber,
 * avec le geste de reconnexion.
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

describe('Grok 0.70.0 P2 : un succès Google efface le message d’agendas devenu faux', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalendarStore.setState({
      calendars: [{ id: 'g1', provider: 'google', account_id: 'a1', summary: 'Ludo', primary: true }] as never,
      currentCalendarId: 'g1', events: [], currentEventId: null, isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [{ id: 'a1', email: 'ludo@example.fr', provider: 'gmail' }] as never, currentAccountId: 'a1', needsReauth: false });
  });

  it('le message du 403 disparaît quand les événements Google se chargent', async () => {
    render(<CalendarPanel standalone />);
    for (let tour = 0; tour < 6; tour++) {
      await act(async () => { await Promise.resolve(); });
    }
    expect(screen.queryByText(new RegExp(CAUSE.slice(0, 40)))).toBeNull();
  });
});
