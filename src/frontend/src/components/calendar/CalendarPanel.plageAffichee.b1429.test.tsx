/**
 * B-1429 (recette P-146, lot 1, 25/09) : un rendez-vous du 30 septembre
 * disparaissait de l'Agenda. La plage demandée allait du 1er du mois au
 * DERNIER JOUR À MINUIT (`new Date(année, mois + 1, 0)`) : le dernier jour
 * était exclu. La grille du mois montre aussi des jours des mois voisins
 * (42 cases), et la vue Semaine à cheval sur deux mois réutilisait la plage
 * du mois de la date choisie.
 *
 * La plage demandée couvre désormais exactement ce que la vue affiche.
 */
import { act, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const { CALENDRIER } = vi.hoisted(() => ({
  CALENDRIER: {
    id: 'cal-1', account_id: null, summary: 'Mon calendrier', description: null,
    timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
  } as never,
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: false, accounts: [] }),
    listCalendars: vi.fn().mockResolvedValue([CALENDRIER]),
    listEvents: vi.fn().mockResolvedValue([]),
  };
});

import { CalendarPanel } from './CalendarPanel';

function derniereplage(): { debut: Date; fin: Date } {
  const appels = vi.mocked(api.listEvents).mock.calls;
  const params = appels[appels.length - 1][2] as { time_min: string; time_max: string };
  return { debut: new Date(params.time_min), fin: new Date(params.time_max) };
}

function preparer(viewMode: 'month' | 'week' | 'day' | 'list', selectedDate: Date) {
  useCalendarStore.setState({
    calendars: [CALENDRIER], currentCalendarId: 'cal-1', events: [], currentEventId: null,
    isEventFormOpen: false, viewMode, selectedDate, draftEvent: {}, showCancelled: false, searchQuery: '',
  });
  useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
}

describe('B-1429 : l’Agenda demande tout ce que la vue affiche', () => {
  beforeEach(() => vi.clearAllMocks());

  it('Mois de septembre 2026 : du lundi 31 août au dimanche 11 octobre inclus', async () => {
    preparer('month', new Date(2026, 8, 15));
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    const { debut, fin } = derniereplage();
    expect(debut.getTime()).toBe(new Date(2026, 7, 31).getTime());
    expect(fin.getTime()).toBe(new Date(2026, 9, 12).getTime());
    // Le rendez-vous du 30 septembre à 9 h est dans la plage.
    expect(new Date(2026, 8, 30, 9).getTime()).toBeLessThan(fin.getTime());
  });

  it('Semaine du 28 septembre : du lundi 28 au dimanche 4 octobre inclus', async () => {
    preparer('week', new Date(2026, 8, 29));
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    const { debut, fin } = derniereplage();
    expect(debut.getTime()).toBe(new Date(2026, 8, 28).getTime());
    expect(fin.getTime()).toBe(new Date(2026, 9, 5).getTime());
  });

  it('Jour : la journée entière', async () => {
    preparer('day', new Date(2026, 8, 30, 15));
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    const { debut, fin } = derniereplage();
    expect(debut.getTime()).toBe(new Date(2026, 8, 30).getTime());
    expect(fin.getTime()).toBe(new Date(2026, 9, 1).getTime());
  });

  it('Liste : le mois, dernier jour compris', async () => {
    preparer('list', new Date(2026, 8, 15));
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    const { debut, fin } = derniereplage();
    expect(debut.getTime()).toBe(new Date(2026, 8, 1).getTime());
    expect(fin.getTime()).toBe(new Date(2026, 9, 1).getTime());
  });

  it('changer de vue recharge la plage de la nouvelle vue', async () => {
    preparer('month', new Date(2026, 8, 29));
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(api.listEvents).toHaveBeenCalled());
    act(() => useCalendarStore.getState().setViewMode('week'));
    await waitFor(() => expect(derniereplage().debut.getTime()).toBe(new Date(2026, 8, 28).getTime()));
    expect(derniereplage().fin.getTime()).toBe(new Date(2026, 9, 5).getTime());
  });
});
